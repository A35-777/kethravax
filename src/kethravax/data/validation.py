"""Dataset validation, leakage checking, and integrity auditing."""

from __future__ import annotations

import hashlib
from typing import Dict, List, Set, Tuple
from kethravax.core.types import SegmentationResult


def compute_stream_hash(data: bytes) -> str:
    """Compute SHA-256 hash of byte stream."""
    return hashlib.sha256(data).hexdigest()


def audit_dataset_splits(
    train_samples: List[Tuple[bytes, SegmentationResult]],
    val_samples: List[Tuple[bytes, SegmentationResult]],
    test_samples: List[Tuple[bytes, SegmentationResult]],
) -> Dict[str, Any]:
    """Audit train/val/test splits for duplicate byte streams and label anomalies.
    
    Returns an audit report dictionary ensuring strict non-leakage.
    """
    train_hashes = {compute_stream_hash(b): i for i, (b, _) in enumerate(train_samples)}
    val_hashes = {compute_stream_hash(b): i for i, (b, _) in enumerate(val_samples)}
    test_hashes = {compute_stream_hash(b): i for i, (b, _) in enumerate(test_samples)}

    train_val_leak = set(train_hashes.keys()) & set(val_hashes.keys())
    train_test_leak = set(train_hashes.keys()) & set(test_hashes.keys())
    val_test_leak = set(val_hashes.keys()) & set(test_hashes.keys())

    has_leakage = bool(train_val_leak or train_test_leak or val_test_leak)

    # Validate segmentation invariants for all samples
    invalid_samples = []
    for split_name, samples in [("train", train_samples), ("val", val_samples), ("test", test_samples)]:
        for idx, (_, seg_res) in enumerate(samples):
            is_valid, err = seg_res.validate_invariants()
            if not is_valid:
                invalid_samples.append({
                    "split": split_name,
                    "sample_idx": idx,
                    "stream_id": seg_res.stream_id,
                    "error": err,
                })

    return {
        "has_leakage": has_leakage,
        "leakage_counts": {
            "train_val": len(train_val_leak),
            "train_test": len(train_test_leak),
            "val_test": len(val_test_leak),
        },
        "sample_counts": {
            "train": len(train_samples),
            "val": len(val_samples),
            "test": len(test_samples),
        },
        "all_invariants_valid": len(invalid_samples) == 0,
        "invalid_samples": invalid_samples,
    }

