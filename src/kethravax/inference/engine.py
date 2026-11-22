"""High-level inference engine for Kethravax structural segmentation."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Union
import numpy as np
import torch

from kethravax.core.taxonomy import (
    ARCH_TO_IDX,
    CATEGORY_TO_IDX,
    IDX_TO_ARCH,
    IDX_TO_CATEGORY,
    STRUCTURAL_CATEGORIES,
)
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.models.baselines import EntropyHeuristicBaseline
from kethravax.models.decoder import StructuralDecoder
from kethravax.models.hybrid import KethraSegHybrid


class BinarySegmenter:
    """High-level neural and statistical segmentation engine for raw binary streams.
    
    Usage:
        segmenter = BinarySegmenter.from_pretrained("default")
        result = segmenter.analyze_file("sample.bin")
        for seg in result.segments:
            print(seg.start, seg.end, seg.category, seg.confidence)
    """

    def __init__(
        self,
        model: Optional[torch.nn.Module] = None,
        decoder: Optional[StructuralDecoder] = None,
        window_size: int = 128,
        stride: int = 64,
        device: str = "cpu",
    ) -> None:
        self.device = device
        self.window_size = window_size
        self.stride = stride
        self.decoder = decoder or StructuralDecoder()
        self.model = model
        if self.model is not None:
            self.model.to(self.device)
            self.model.eval()

        self.fallback_heuristic = EntropyHeuristicBaseline()

    @classmethod
    def from_pretrained(cls, model_name: str = "default", device: str = "cpu") -> "BinarySegmenter":
        """Load a pretrained KethraSeg model from local weights."""
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "models", "weights"))
        weights_path = os.path.join(base_dir, "kethraseg_hybrid.pt")

        model = KethraSegHybrid(embedding_dim=48, conv_branch_channels=12, rnn_hidden_dim=36)
        if os.path.exists(weights_path):
            state_dict = torch.load(weights_path, map_location=device, weights_only=True)
            model.load_state_dict(state_dict)

        return cls(model=model, device=device)

    def analyze_bytes(self, data: bytes, stream_id: str = "input_stream") -> SegmentationResult:
        """Perform multi-class structural segmentation on an in-memory byte sequence."""
        length = len(data)
        if length == 0:
            return SegmentationResult(stream_id=stream_id, total_bytes=0, segments=[])

        if self.model is None:
            return self.fallback_heuristic.analyze_bytes(data, stream_id=stream_id)

        # Sliding window inference
        num_cats = len(STRUCTURAL_CATEGORIES)
        num_archs = len(IDX_TO_ARCH)

        cat_accum = np.zeros((length, num_cats), dtype=np.float32)
        arch_accum = np.zeros((length, num_archs), dtype=np.float32)
        bnd_accum = np.zeros(length, dtype=np.float32)
        counts = np.zeros(length, dtype=np.float32)

        offsets = list(range(0, max(1, length - self.window_size + 1), self.stride))
        if offsets[-1] + self.window_size < length:
            offsets.append(length - self.window_size)

        # Batch windows for CPU efficiency
        batch_size = 32
        with torch.no_grad():
            for b_idx in range(0, len(offsets), batch_size):
                batch_offsets = offsets[b_idx : b_idx + batch_size]
                batch_chunks = []
                actual_lens = []

                for off in batch_offsets:
                    chunk = data[off : off + self.window_size]
                    actual_lens.append(len(chunk))
                    pad_chunk = chunk + bytes([0] * (self.window_size - len(chunk)))
                    batch_chunks.append(np.frombuffer(pad_chunk, dtype=np.uint8))

                batch_arr = np.stack(batch_chunks)
                b_tensor = torch.from_numpy(batch_arr).long().to(self.device)
                cat_logits, arch_logits, bnd_logits = self.model(b_tensor)

                cat_probs = torch.softmax(cat_logits, dim=-1).cpu().numpy()
                arch_probs = torch.softmax(arch_logits, dim=-1).cpu().numpy()
                bnd_probs = torch.sigmoid(bnd_logits).cpu().numpy()

                for i, off in enumerate(batch_offsets):
                    act_len = actual_lens[i]
                    cat_accum[off : off + act_len] += cat_probs[i, :act_len]
                    arch_accum[off : off + act_len] += arch_probs[i, :act_len]
                    bnd_accum[off : off + act_len] += bnd_probs[i, :act_len]
                    counts[off : off + act_len] += 1.0

        counts = np.maximum(counts, 1.0)[:, None]
        norm_cat_probs = cat_accum / counts
        norm_arch_probs = arch_accum / counts
        norm_bnd_probs = bnd_accum / counts.squeeze(-1)

        return self.decoder.decode_stream(
            data_bytes=data,
            cat_probs=norm_cat_probs,
            arch_probs=norm_arch_probs,
            boundary_probs=norm_bnd_probs,
            stream_id=stream_id,
            metadata={"engine": "KethraSegHybrid", "device": self.device},
        )

    def analyze_file(self, file_path: str) -> SegmentationResult:
        """Perform multi-class structural segmentation on a file on disk."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Input file not found: {file_path}")

        stream_id = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            data = f.read()

        return self.analyze_bytes(data, stream_id=stream_id)

