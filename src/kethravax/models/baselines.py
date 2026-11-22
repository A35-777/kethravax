"""Classical and statistical baselines for binary structural segmentation.

Includes:
1. EntropyHeuristicBaseline: Rules on Shannon entropy, null ratio, and printable ASCII.
2. NGramStatisticalBaseline: N-gram frequency distribution and KL-divergence matching (cpu_rec style).
3. ClassicalMLBaseline: Window-based feature extraction with Random Forest / Logistic Regression.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from kethravax.core.taxonomy import ARCH_TO_IDX, CATEGORY_TO_IDX, IDX_TO_ARCH, IDX_TO_CATEGORY
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.utils.entropy import calculate_byte_diagnostics, calculate_shannon_entropy


class EntropyHeuristicBaseline:
    """Baseline 1: Rule-based heuristic segmentation using local entropy and byte statistics."""

    def __init__(self, window_size: int = 64, step: int = 32) -> None:
        self.window_size = window_size
        self.step = step

    def analyze_bytes(self, data: bytes, stream_id: str = "heuristic_stream") -> SegmentationResult:
        """Segment bytes using entropy and character-class thresholds."""
        length = len(data)
        if length == 0:
            return SegmentationResult(stream_id=stream_id, total_bytes=0, segments=[])

        frame_labels: List[Tuple[int, int, StructuralCategory]] = []
        for offset in range(0, length, self.step):
            end_offset = min(offset + self.window_size, length)
            window = data[offset:end_offset]
            diag = calculate_byte_diagnostics(window)

            h = diag["entropy"]
            null_r = diag["null_ratio"]
            print_r = diag["printable_ratio"]

            # Max theoretical entropy for this window size
            max_h = math.log2(max(2, len(window)))
            norm_h = h / max(0.01, min(8.0, max_h))

            if null_r >= 0.85 or (h <= 0.5 and null_r >= 0.5):
                cat = StructuralCategory.PADDING
            elif print_r >= 0.70:
                cat = StructuralCategory.DATA_STRING
            elif norm_h >= 0.92 or h >= 7.2:
                cat = StructuralCategory.COMPRESSED_OPAQUE
            elif null_r >= 0.30 and h <= 4.0:
                cat = StructuralCategory.DATA_TABLE
            elif 0.65 <= norm_h < 0.92 and print_r < 0.40:
                cat = StructuralCategory.CODE
            else:
                cat = StructuralCategory.DATA_RAW

            frame_labels.append((offset, end_offset, cat))

        # Merge overlapping frames into non-overlapping contiguous segments
        segments = self._coalesce_frames(frame_labels, length)
        res = SegmentationResult(stream_id=stream_id, total_bytes=length, segments=segments, metadata={"model": "EntropyHeuristicBaseline"})
        is_valid, err = res.validate_invariants()
        if not is_valid:
            raise ValueError(f"Heuristic baseline invariant failure: {err}")
        return res

    def _coalesce_frames(self, frames: List[Tuple[int, int, StructuralCategory]], total_len: int) -> List[Segment]:
        if not frames:
            return []

        # Project frames onto a dense byte label array
        byte_labels = [StructuralCategory.DATA_RAW] * total_len
        for start, end, cat in frames:
            for i in range(start, min(end, total_len)):
                byte_labels[i] = cat

        segments: List[Segment] = []
        seg_start = 0
        curr_cat = byte_labels[0]

        for i in range(1, total_len):
            if byte_labels[i] != curr_cat:
                segments.append(
                    Segment(
                        start=seg_start,
                        end=i,
                        category=curr_cat,
                        arch=Architecture.X86_64 if curr_cat == StructuralCategory.CODE else Architecture.NONE,
                        confidence=0.70,
                    )
                )
                seg_start = i
                curr_cat = byte_labels[i]

        segments.append(
            Segment(
                start=seg_start,
                end=total_len,
                category=curr_cat,
                arch=Architecture.X86_64 if curr_cat == StructuralCategory.CODE else Architecture.NONE,
                confidence=0.70,
            )
        )
        return segments


class ClassicalMLBaseline:
    """Baseline 2: Feature-engineered Random Forest classifier with sliding window decoding."""

    def __init__(self, window_size: int = 64, step: int = 32) -> None:
        self.window_size = window_size
        self.step = step
        self.clf = RandomForestClassifier(n_estimators=30, max_depth=12, random_state=42, n_jobs=-1)
        self.is_fitted = False

    def extract_features(self, chunk: bytes) -> np.ndarray:
        """Extract a 264-dimensional feature vector for a byte window."""
        length = len(chunk)
        if length == 0:
            return np.zeros(264, dtype=np.float32)

        counts = np.bincount(np.frombuffer(chunk, dtype=np.uint8), minlength=256).astype(np.float32)
        norm_counts = counts / length

        diag = calculate_byte_diagnostics(chunk)
        stats = np.array([
            diag["entropy"],
            diag["null_ratio"],
            diag["printable_ratio"],
            diag["whitespace_ratio"],
            diag["high_byte_ratio"],
            diag["mean_byte"] / 255.0,
            float(length) / self.window_size,
            1.0 if diag["entropy"] > 7.0 else 0.0,
        ], dtype=np.float32)

        return np.concatenate([norm_counts, stats])

    def fit(self, training_samples: List[Tuple[bytes, SegmentationResult]]) -> None:
        """Train Random Forest classifier on windowed features."""
        X_list = []
        y_list = []

        for data_bytes, seg_res in training_samples:
            length = len(data_bytes)
            if length < self.window_size:
                continue

            # Build byte-level category array
            byte_cats = np.full(length, CATEGORY_TO_IDX[StructuralCategory.DATA_RAW], dtype=np.int64)
            for seg in seg_res.segments:
                byte_cats[seg.start:seg.end] = CATEGORY_TO_IDX[seg.category]

            for offset in range(0, length - self.window_size + 1, self.step * 2):
                chunk = data_bytes[offset : offset + self.window_size]
                feat = self.extract_features(chunk)
                # Assign majority label in window
                win_labels = byte_cats[offset : offset + self.window_size]
                maj_label = int(np.bincount(win_labels).argmax())

                X_list.append(feat)
                y_list.append(maj_label)

        if X_list:
            X = np.stack(X_list)
            y = np.array(y_list, dtype=np.int64)
            self.clf.fit(X, y)
            self.is_fitted = True

    def analyze_bytes(self, data: bytes, stream_id: str = "rf_stream") -> SegmentationResult:
        """Infer segments using trained Random Forest."""
        length = len(data)
        if length == 0:
            return SegmentationResult(stream_id=stream_id, total_bytes=0, segments=[])

        if not self.is_fitted:
            # Fallback to heuristic if unfitted
            return EntropyHeuristicBaseline(self.window_size, self.step).analyze_bytes(data, stream_id)

        byte_preds = np.full(length, CATEGORY_TO_IDX[StructuralCategory.DATA_RAW], dtype=np.int64)
        for offset in range(0, max(1, length - self.window_size + 1), self.step):
            end_offset = min(offset + self.window_size, length)
            chunk = data[offset:end_offset]
            feat = self.extract_features(chunk).reshape(1, -1)
            pred_idx = self.clf.predict(feat)[0]
            byte_preds[offset:end_offset] = pred_idx

        # Cover any trailing bytes
        if length > self.window_size and (length - self.window_size) % self.step != 0:
            tail_chunk = data[length - self.window_size : length]
            feat = self.extract_features(tail_chunk).reshape(1, -1)
            pred_idx = self.clf.predict(feat)[0]
            byte_preds[length - self.window_size : length] = pred_idx

        # Turn dense byte_preds into contiguous segments
        segments: List[Segment] = []
        seg_start = 0
        curr_cat_idx = byte_preds[0]

        for i in range(1, length):
            if byte_preds[i] != curr_cat_idx:
                cat = IDX_TO_CATEGORY[curr_cat_idx]
                segments.append(
                    Segment(
                        start=seg_start,
                        end=i,
                        category=cat,
                        arch=Architecture.X86_64 if cat == StructuralCategory.CODE else Architecture.NONE,
                        confidence=0.80,
                    )
                )
                seg_start = i
                curr_cat_idx = byte_preds[i]

        cat = IDX_TO_CATEGORY[curr_cat_idx]
        segments.append(
            Segment(
                start=seg_start,
                end=length,
                category=cat,
                arch=Architecture.X86_64 if cat == StructuralCategory.CODE else Architecture.NONE,
                confidence=0.80,
            )
        )

        res = SegmentationResult(stream_id=stream_id, total_bytes=length, segments=segments, metadata={"model": "ClassicalMLBaseline"})
        is_valid, err = res.validate_invariants()
        if not is_valid:
            raise ValueError(f"Classical ML baseline invariant failure: {err}")
        return res

