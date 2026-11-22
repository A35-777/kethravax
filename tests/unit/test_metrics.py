"""Unit tests for binary metrics and boundary localization."""

import pytest
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.utils.metrics import compute_byte_segmentation_metrics


def test_metrics_perfect_match() -> None:
    s1 = Segment(start=0, end=50, category=StructuralCategory.CODE, arch=Architecture.X86_64)
    s2 = Segment(start=50, end=100, category=StructuralCategory.PADDING)
    gt = SegmentationResult(stream_id="gt", total_bytes=100, segments=[s1, s2])
    pred = SegmentationResult(stream_id="pred", total_bytes=100, segments=[s1, s2])

    metrics = compute_byte_segmentation_metrics(gt, pred)
    assert metrics["overall_byte_accuracy"] == 1.0
    assert metrics["macro_f1"] == 1.0
    assert metrics["boundary_localization"]["tol_0B"]["f1"] == 1.0
    assert metrics["boundary_localization"]["tol_4B"]["f1"] == 1.0


def test_metrics_boundary_jitter() -> None:
    # True boundary at 50, prediction boundary at 52 (within 4 bytes)
    s1_gt = Segment(start=0, end=50, category=StructuralCategory.CODE, arch=Architecture.X86_64)
    s2_gt = Segment(start=50, end=100, category=StructuralCategory.PADDING)
    gt = SegmentationResult(stream_id="gt", total_bytes=100, segments=[s1_gt, s2_gt])

    s1_pred = Segment(start=0, end=52, category=StructuralCategory.CODE, arch=Architecture.X86_64)
    s2_pred = Segment(start=52, end=100, category=StructuralCategory.PADDING)
    pred = SegmentationResult(stream_id="pred", total_bytes=100, segments=[s1_pred, s2_pred])

    metrics = compute_byte_segmentation_metrics(gt, pred)
    # Overall byte accuracy is 98/100 = 0.98
    assert metrics["overall_byte_accuracy"] == 0.98
    # Exact 0B boundary F1 should be 0.0 because offset 52 != 50
    assert metrics["boundary_localization"]["tol_0B"]["f1"] == 0.0
    # Tolerance 4B boundary F1 should be 1.0 because |52 - 50| = 2 <= 4!
    assert metrics["boundary_localization"]["tol_4B"]["f1"] == 1.0

