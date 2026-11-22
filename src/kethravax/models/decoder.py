"""Structured decoding, boundary refinement, and exact offset recovery."""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import torch
import torch.nn.functional as F

from kethravax.core.taxonomy import (
    ARCH_TO_IDX,
    CATEGORY_TO_IDX,
    IDX_TO_ARCH,
    IDX_TO_CATEGORY,
    STRUCTURAL_CATEGORIES,
)
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.utils.entropy import calculate_byte_diagnostics


class StructuralDecoder:
    """Decodes dense token-level predictions into contiguous, invariant-preserving segments.
    
    Features:
        - Exact byte preservation from offset 0 to EOF.
        - Boundary snapping using boundary head probability and byte gradient discontinuities.
        - Uncertainty estimation: low-confidence regions are assigned UNKNOWN_AMBIGUOUS.
    """

    def __init__(
        self,
        confidence_threshold: float = 0.40,
        boundary_threshold: float = 0.50,
        min_segment_length: int = 16,
    ) -> None:
        self.confidence_threshold = confidence_threshold
        self.boundary_threshold = boundary_threshold
        self.min_segment_length = min_segment_length

    def decode_stream(
        self,
        data_bytes: bytes,
        cat_probs: np.ndarray,
        arch_probs: np.ndarray,
        boundary_probs: Optional[np.ndarray] = None,
        stream_id: str = "decoded_stream",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SegmentationResult:
        """Decode dense probability arrays into non-overlapping contiguous segments.
        
        Args:
            data_bytes: The raw input bytes of length N.
            cat_probs: Array of shape (N, num_categories).
            arch_probs: Array of shape (N, num_architectures).
            boundary_probs: Optional array of shape (N,) with boundary transition scores.
            stream_id: Identifier string.
            metadata: Optional metadata dict.
        """
        length = len(data_bytes)
        if length == 0:
            return SegmentationResult(stream_id=stream_id, total_bytes=0, segments=[])

        if len(cat_probs) != length:
            raise ValueError(f"cat_probs length ({len(cat_probs)}) must match byte length ({length})")

        # 1. Determine raw byte predictions and confidence
        raw_cats: List[StructuralCategory] = []
        raw_archs: List[Architecture] = []
        confidences: List[float] = []

        for i in range(length):
            p_cat = cat_probs[i]
            max_p = float(np.max(p_cat))
            best_cat_idx = int(np.argmax(p_cat))
            best_cat = IDX_TO_CATEGORY[best_cat_idx]

            # Uncertainty check
            if max_p < self.confidence_threshold:
                cat = StructuralCategory.UNKNOWN_AMBIGUOUS
                arch = Architecture.NONE
                conf = max_p
            else:
                cat = best_cat
                if cat == StructuralCategory.CODE and arch_probs is not None:
                    best_arch_idx = int(np.argmax(arch_probs[i]))
                    arch = IDX_TO_ARCH[best_arch_idx]
                else:
                    arch = Architecture.NONE
                conf = max_p

            raw_cats.append(cat)
            raw_archs.append(arch)
            confidences.append(conf)

        # 2. Identify candidate boundary transition points
        candidate_cuts: List[int] = [0]

        # Scan for label transitions
        for i in range(1, length):
            cat_changed = raw_cats[i] != raw_cats[i - 1]
            arch_changed = (raw_cats[i] == StructuralCategory.CODE and raw_archs[i] != raw_archs[i - 1])

            is_boundary = cat_changed or arch_changed
            if boundary_probs is not None and boundary_probs[i] >= self.boundary_threshold:
                is_boundary = True

            if is_boundary:
                # Snap boundary to local byte discontinuity (null run transition, ASCII edge, etc.)
                snapped_offset = self._snap_boundary(data_bytes, i, search_radius=4)
                if snapped_offset > candidate_cuts[-1]:
                    candidate_cuts.append(snapped_offset)

        if candidate_cuts[-1] != length:
            candidate_cuts.append(length)

        # Deduplicate and sort cuts
        candidate_cuts = sorted(list(set(candidate_cuts)))
        if candidate_cuts[0] != 0:
            candidate_cuts.insert(0, 0)
        if candidate_cuts[-1] != length:
            candidate_cuts.append(length)

        # 3. Form raw segments
        raw_segments: List[Segment] = []
        for j in range(len(candidate_cuts) - 1):
            start = candidate_cuts[j]
            end = candidate_cuts[j + 1]
            if end <= start:
                continue

            chunk = data_bytes[start:end]
            chunk_cats = raw_cats[start:end]
            chunk_archs = raw_archs[start:end]
            chunk_confs = confidences[start:end]

            # Majority voting in segment interval
            cat_counts: Dict[StructuralCategory, int] = {}
            for c in chunk_cats:
                cat_counts[c] = cat_counts.get(c, 0) + 1
            majority_cat = max(cat_counts.items(), key=lambda kv: kv[1])[0]

            if majority_cat == StructuralCategory.CODE:
                arch_counts: Dict[Architecture, int] = {}
                for a in chunk_archs:
                    if a != Architecture.NONE:
                        arch_counts[a] = arch_counts.get(a, 0) + 1
                majority_arch = max(arch_counts.items(), key=lambda kv: kv[1])[0] if arch_counts else Architecture.X86_64
            else:
                majority_arch = Architecture.NONE

            avg_conf = float(np.mean(chunk_confs))
            diag = calculate_byte_diagnostics(chunk)

            raw_segments.append(
                Segment(
                    start=start,
                    end=end,
                    category=majority_cat,
                    arch=majority_arch,
                    confidence=avg_conf,
                    diagnostics=diag,
                )
            )

        # 4. Merge adjacent segments with identical (category, arch)
        final_segments: List[Segment] = []
        for s in raw_segments:
            if not final_segments:
                final_segments.append(s)
            else:
                last = final_segments[-1]
                if last.category == s.category and last.arch == s.arch:
                    combined_diag = calculate_byte_diagnostics(data_bytes[last.start:s.end])
                    final_segments[-1] = Segment(
                        start=last.start,
                        end=s.end,
                        category=last.category,
                        arch=last.arch,
                        confidence=(last.confidence * last.length + s.confidence * s.length) / (last.length + s.length),
                        diagnostics=combined_diag,
                    )
                else:
                    final_segments.append(s)

        res = SegmentationResult(
            stream_id=stream_id,
            total_bytes=length,
            segments=final_segments,
            metadata=metadata or {},
        )

        is_valid, err = res.validate_invariants()
        if not is_valid:
            raise ValueError(f"Decoder invariant failure: {err}")

        return res

    def _snap_boundary(self, data: bytes, target_offset: int, search_radius: int = 4) -> int:
        """Snap coarse boundary to exact byte discontinuity within a local radius."""
        start = max(1, target_offset - search_radius)
        end = min(len(data) - 1, target_offset + search_radius)

        best_offset = target_offset
        best_score = -1.0

        for off in range(start, end + 1):
            left_b = data[off - 1]
            right_b = data[off]

            score = 0.0
            # Discontinuity: null boundary (e.g. 0x00 followed by non-zero or vice-versa)
            if (left_b == 0 and right_b != 0) or (left_b != 0 and right_b == 0):
                score += 2.0
            # Discontinuity: printable ASCII to non-printable
            left_print = 0x20 <= left_b <= 0x7E
            right_print = 0x20 <= right_b <= 0x7E
            if left_print != right_print:
                score += 1.5

            # Alignment bonus (multiples of 4, 8, 16)
            if off % 16 == 0:
                score += 1.0
            elif off % 4 == 0:
                score += 0.5

            # Distance penalty
            dist = abs(off - target_offset)
            score -= dist * 0.1

            if score > best_score:
                best_score = score
                best_offset = off

        return best_offset

