"""Unit tests for Kethravax core types, invariants, and taxonomy."""

import json
import pytest
from kethravax.core.taxonomy import (
    ARCH_TO_IDX,
    CATEGORY_TO_IDX,
    IDX_TO_ARCH,
    IDX_TO_CATEGORY,
    STRUCTURAL_CATEGORIES,
)
from kethravax.core.types import (
    Architecture,
    Segment,
    SegmentationResult,
    StructuralCategory,
)


def test_segment_validation() -> None:
    # Valid segment
    seg = Segment(start=0, end=100, category=StructuralCategory.CODE, arch=Architecture.X86_64, confidence=0.95)
    assert seg.length == 100
    assert seg.confidence == 0.95

    # Non-code segment should reset arch to NONE
    seg_data = Segment(start=100, end=200, category=StructuralCategory.DATA_STRING, arch=Architecture.X86_64)
    assert seg_data.arch == Architecture.NONE

    # Invalid start / end
    with pytest.raises(ValueError):
        Segment(start=100, end=50, category=StructuralCategory.PADDING)

    with pytest.raises(ValueError):
        Segment(start=-1, end=50, category=StructuralCategory.PADDING)


def test_segmentation_result_invariants() -> None:
    # Perfectly valid result
    s1 = Segment(start=0, end=50, category=StructuralCategory.CODE, arch=Architecture.X86_64)
    s2 = Segment(start=50, end=100, category=StructuralCategory.PADDING)
    res = SegmentationResult(stream_id="valid", total_bytes=100, segments=[s1, s2])

    is_valid, err = res.validate_invariants()
    assert is_valid is True
    assert err is None

    # Test JSON serialization roundtrip
    d = res.to_dict()
    assert d["total_bytes"] == 100
    assert len(d["segments"]) == 2

    res_restored = SegmentationResult.from_dict(d)
    assert res_restored.total_bytes == 100
    assert res_restored.segments[0].category == StructuralCategory.CODE

    # Discontinuity failure
    s_bad = Segment(start=60, end=100, category=StructuralCategory.PADDING)
    res_bad = SegmentationResult(stream_id="bad", total_bytes=100, segments=[s1, s_bad])
    is_valid_bad, err_bad = res_bad.validate_invariants()
    assert is_valid_bad is False
    assert "Discontinuity" in err_bad

    # Under-coverage failure
    res_under = SegmentationResult(stream_id="under", total_bytes=120, segments=[s1, s2])
    is_valid_under, err_under = res_under.validate_invariants()
    assert is_valid_under is False
    assert "Final segment end offset" in err_under


def test_empty_stream() -> None:
    res = SegmentationResult(stream_id="empty", total_bytes=0, segments=[])
    is_valid, err = res.validate_invariants()
    assert is_valid is True
    assert err is None

