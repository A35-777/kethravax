"""Integration tests for the complete Kethravax analysis pipeline."""

import pytest
from kethravax.core.types import StructuralCategory
from kethravax.data.synthetic import generate_synthetic_stream
from kethravax.inference.engine import BinarySegmenter


def test_full_pipeline_synthetic_stream() -> None:
    # Generate test stream
    data_bytes, _ = generate_synthetic_stream("integ_stream", target_total_bytes=2048, seed=777)

    segmenter = BinarySegmenter()
    result = segmenter.analyze_bytes(data_bytes, stream_id="integ_stream")

    assert result.total_bytes == 2048
    assert len(result.segments) > 0

    # Invariants must hold strictly
    is_valid, err = result.validate_invariants()
    assert is_valid is True, f"Invariant failed: {err}"

    # JSON export validation
    json_str = result.to_json()
    assert "integ_stream" in json_str
    assert "segments" in json_str

