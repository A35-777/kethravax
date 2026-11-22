"""PyTorch dataset and data loaders for multi-class byte-stream segmentation."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple
import numpy as np
import torch
from torch.utils.data import Dataset

from kethravax.core.taxonomy import (
    ARCH_TO_IDX,
    CATEGORY_TO_IDX,
    IDX_TO_ARCH,
    IDX_TO_CATEGORY,
    STRUCTURAL_CATEGORIES,
)
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory


class BinaryStreamDataset(Dataset):
    """PyTorch Dataset that extracts fixed-size windowed slices from binary streams.
    
    Each sample returns:
        - bytes: Tensor of shape (window_size,) dtype=torch.long in [0, 255]
        - cat_labels: Tensor of shape (window_size,) dtype=torch.long in [0, num_classes-1]
        - arch_labels: Tensor of shape (window_size,) dtype=torch.long in [0, num_archs-1]
        - boundary_targets: Tensor of shape (window_size,) dtype=torch.float in {0.0, 1.0}
        - ambiguity_mask: Tensor of shape (window_size,) dtype=torch.bool (True = valid, False = ignore)
    """

    def __init__(
        self,
        samples: List[Tuple[bytes, SegmentationResult]],
        window_size: int = 128,
        stride: int = 64,
    ) -> None:
        self.window_size = window_size
        self.stride = stride
        self.windows: List[Tuple[int, int]] = []  # List of (sample_idx, byte_offset)
        self.samples = samples

        self._build_index()

    def _build_index(self) -> None:
        """Slice all streams into windowed offsets."""
        self.windows.clear()
        for sample_idx, (data_bytes, seg_res) in enumerate(self.samples):
            length = len(data_bytes)
            if length == 0:
                continue
            if length <= self.window_size:
                self.windows.append((sample_idx, 0))
            else:
                for offset in range(0, length - self.window_size + 1, self.stride):
                    self.windows.append((sample_idx, offset))
                # Add trailing window if remainder exists
                if (length - self.window_size) % self.stride != 0:
                    self.windows.append((sample_idx, length - self.window_size))

    def __len__(self) -> int:
        return len(self.windows)

    def __getitem__(self, idx: int) -> Dict[str, torch.Tensor]:
        sample_idx, offset = self.windows[idx]
        data_bytes, seg_res = self.samples[sample_idx]

        length = len(data_bytes)
        end_offset = min(offset + self.window_size, length)
        chunk = data_bytes[offset:end_offset]

        # Allocate arrays
        byte_arr = np.zeros(self.window_size, dtype=np.int64)
        cat_arr = np.full(self.window_size, CATEGORY_TO_IDX[StructuralCategory.PADDING], dtype=np.int64)
        arch_arr = np.full(self.window_size, ARCH_TO_IDX[Architecture.NONE], dtype=np.int64)
        bnd_arr = np.zeros(self.window_size, dtype=np.float32)
        mask_arr = np.ones(self.window_size, dtype=bool)

        actual_len = len(chunk)
        byte_arr[:actual_len] = np.frombuffer(chunk, dtype=np.uint8)
        if actual_len < self.window_size:
            mask_arr[actual_len:] = False  # Ignore padding in loss

        # Map ground-truth segments into dense window labels
        for seg in seg_res.segments:
            # Check overlap with [offset, offset + actual_len)
            overlap_start = max(seg.start, offset)
            overlap_end = min(seg.end, offset + actual_len)
            if overlap_start < overlap_end:
                win_start = overlap_start - offset
                win_end = overlap_end - offset
                cat_idx = CATEGORY_TO_IDX[seg.category]
                arch_idx = ARCH_TO_IDX[seg.arch]
                cat_arr[win_start:win_end] = cat_idx
                arch_arr[win_start:win_end] = arch_idx

                # If this segment is UNKNOWN_AMBIGUOUS, mask it out from strict loss
                if seg.category == StructuralCategory.UNKNOWN_AMBIGUOUS:
                    mask_arr[win_start:win_end] = False

                # Mark boundary transition if start falls inside window
                if offset < seg.start < offset + actual_len:
                    bnd_idx = seg.start - offset
                    bnd_arr[bnd_idx] = 1.0

        return {
            "bytes": torch.from_numpy(byte_arr),
            "cat_labels": torch.from_numpy(cat_arr),
            "arch_labels": torch.from_numpy(arch_arr),
            "boundary_targets": torch.from_numpy(bnd_arr),
            "ambiguity_mask": torch.from_numpy(mask_arr),
        }

