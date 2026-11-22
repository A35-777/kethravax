"""Regression tests for edge cases, unusual byte patterns, and corrupt streams."""

import pytest
from kethravax.core.types import StructuralCategory
from kethravax.inference.engine import BinarySegmenter


def test_edge_case_empty_bytes() -> None:
    segmenter = BinarySegmenter()
    res = segmenter.analyze_bytes(b"", stream_id="empty")
    assert res.total_bytes == 0
    assert len(res.segments) == 0


def test_edge_case_single_byte() -> None:
    segmenter = BinarySegmenter()
    res = segmenter.analyze_bytes(b"\x90", stream_id="one_byte")
    assert res.total_bytes == 1
    assert len(res.segments) == 1
    assert res.segments[0].start == 0
    assert res.segments[0].end == 1


def test_edge_case_all_zeros() -> None:
    segmenter = BinarySegmenter()
    data = bytes([0x00] * 256)
    res = segmenter.analyze_bytes(data, stream_id="all_zeros")
    assert res.total_bytes == 256
    assert res.segments[0].category == StructuralCategory.PADDING


def test_edge_case_high_entropy_random() -> None:
    import random
    rng = random.Random(999)
    data = rng.randbytes(512)

    segmenter = BinarySegmenter()
    res = segmenter.analyze_bytes(data, stream_id="random_noise")
    assert res.total_bytes == 512
    # Should detect high-entropy as COMPRESSED_OPAQUE or UNKNOWN_AMBIGUOUS
    assert res.segments[0].category in (StructuralCategory.COMPRESSED_OPAQUE, StructuralCategory.UNKNOWN_AMBIGUOUS, StructuralCategory.DATA_RAW)

