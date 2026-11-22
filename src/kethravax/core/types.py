"""Core types and data structures for Kethravax structural segmentation."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class StructuralCategory(str, Enum):
    """Primary structural category taxonomy for binary byte streams."""
    CODE = "CODE"
    DATA_STRING = "DATA_STRING"
    DATA_TABLE = "DATA_TABLE"
    DATA_RAW = "DATA_RAW"
    PADDING = "PADDING"
    COMPRESSED_OPAQUE = "COMPRESSED_OPAQUE"
    UNKNOWN_AMBIGUOUS = "UNKNOWN_AMBIGUOUS"

    @classmethod
    def from_str(cls, val: str) -> "StructuralCategory":
        val_upper = val.strip().upper()
        for member in cls:
            if member.value == val_upper:
                return member
        return cls.UNKNOWN_AMBIGUOUS


class Architecture(str, Enum):
    """Instruction Set Architecture taxonomy (active when category is CODE)."""
    NONE = "NONE"
    X86_64 = "x86_64"
    X86_32 = "x86_32"
    ARM32_ARM = "arm32_arm"
    ARM32_THUMB = "arm32_thumb"
    AARCH64 = "aarch64"
    MIPS32 = "mips32"
    RISCV = "riscv"
    ARCH_UNKNOWN = "arch_unknown"

    @classmethod
    def from_str(cls, val: str) -> "Architecture":
        val_lower = val.strip().lower()
        for member in cls:
            if member.value.lower() == val_lower:
                return member
        return cls.NONE


@dataclass
class Segment:
    """A contiguous byte-range segment with structural and architectural predictions.
    
    Attributes:
        start: Inclusive start offset in the byte stream (>= 0).
        end: Exclusive end offset in the byte stream (> start).
        category: Predicted structural category.
        arch: Predicted architecture (if category is CODE, else NONE).
        confidence: Calibrated model confidence in [0.0, 1.0].
        diagnostics: Diagnostic metrics (entropy, byte distribution, alternative predictions).
    """
    start: int
    end: int
    category: StructuralCategory
    arch: Architecture = Architecture.NONE
    confidence: float = 1.0
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.start < 0:
            raise ValueError(f"Segment start offset must be non-negative, got {self.start}")
        if self.end <= self.start:
            raise ValueError(f"Segment end ({self.end}) must be strictly greater than start ({self.start})")
        if not (0.0 <= self.confidence <= 1.0):
            self.confidence = max(0.0, min(1.0, float(self.confidence)))
        if isinstance(self.category, str):
            self.category = StructuralCategory.from_str(self.category)
        if isinstance(self.arch, str):
            self.arch = Architecture.from_str(self.arch)
        if self.category != StructuralCategory.CODE and self.arch != Architecture.NONE:
            # Non-code segments should not carry an active ISA
            self.arch = Architecture.NONE

    @property
    def length(self) -> int:
        """Byte length of the segment."""
        return self.end - self.start

    def to_dict(self) -> Dict[str, Any]:
        """Convert segment to JSON-serializable dictionary."""
        return {
            "start": self.start,
            "end": self.end,
            "length": self.length,
            "category": self.category.value,
            "arch": self.arch.value,
            "confidence": round(float(self.confidence), 4),
            "diagnostics": self.diagnostics,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Segment":
        return cls(
            start=int(data["start"]),
            end=int(data["end"]),
            category=StructuralCategory.from_str(data["category"]),
            arch=Architecture.from_str(data.get("arch", "NONE")),
            confidence=float(data.get("confidence", 1.0)),
            diagnostics=data.get("diagnostics", {}),
        )


@dataclass
class SegmentationResult:
    """Full segmentation result for a binary stream.
    
    Guarantees:
        - Exact byte preservation: start_0 == 0, end_(M-1) == total_bytes.
        - Non-overlapping contiguity: end_k == start_(k+1).
        - No zero-length segments.
    """
    stream_id: str
    total_bytes: int
    segments: List[Segment]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate_invariants(self) -> Tuple[bool, Optional[str]]:
        """Validate structural segmentation invariants."""
        if self.total_bytes < 0:
            return False, f"total_bytes must be >= 0, got {self.total_bytes}"
        if self.total_bytes == 0:
            if len(self.segments) == 0:
                return True, None
            return False, "0-byte stream must have 0 segments"
        if len(self.segments) == 0:
            return False, f"Non-empty stream ({self.total_bytes} bytes) has 0 segments"

        # Check total coverage
        if self.segments[0].start != 0:
            return False, f"First segment start offset is {self.segments[0].start}, expected 0"
        if self.segments[-1].end != self.total_bytes:
            return False, f"Final segment end offset is {self.segments[-1].end}, expected total_bytes {self.total_bytes}"

        # Check contiguity & disjointness
        for i in range(len(self.segments) - 1):
            curr_seg = self.segments[i]
            next_seg = self.segments[i + 1]
            if curr_seg.end != next_seg.start:
                return False, (
                    f"Discontinuity between segment {i} [end={curr_seg.end}] "
                    f"and segment {i+1} [start={next_seg.start}]"
                )

        return True, None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize complete result to dictionary."""
        is_valid, error = self.validate_invariants()
        return {
            "stream_id": self.stream_id,
            "total_bytes": self.total_bytes,
            "segment_count": len(self.segments),
            "is_valid_coverage": is_valid,
            "validation_error": error,
            "metadata": self.metadata,
            "segments": [s.to_dict() for s in self.segments],
        }

    def to_json(self, indent: int = 2) -> str:
        """Export to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SegmentationResult":
        segments = [Segment.from_dict(s) for s in data.get("segments", [])]
        return cls(
            stream_id=str(data.get("stream_id", "unknown")),
            total_bytes=int(data.get("total_bytes", 0)),
            segments=segments,
            metadata=data.get("metadata", {}),
        )

