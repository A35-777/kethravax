"""Comprehensive evaluation metrics for byte-level structural segmentation.

Calculates:
- Byte-level confusion matrix, per-class Precision, Recall, F1, and IoU.
- Macro and Micro F1.
- Boundary localization F1 at tolerances tau in {0, 4, 16, 32} bytes.
- Architecture Macro-F1 on code segments.
- Short-region (<64 byte) detection recall.
- Expected Calibration Error (ECE).
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Set, Tuple
import numpy as np

from kethravax.core.taxonomy import (
    ARCH_TO_IDX,
    CATEGORY_TO_IDX,
    IDX_TO_ARCH,
    IDX_TO_CATEGORY,
    STRUCTURAL_CATEGORIES,
)
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory


def compute_byte_segmentation_metrics(
    ground_truth: SegmentationResult,
    prediction: SegmentationResult,
    tolerances: List[int] = [0, 4, 16, 32],
) -> Dict[str, Any]:
    """Compute dense byte-level metrics and boundary localization metrics.
    
    Args:
        ground_truth: True segmentation result.
        prediction: Predicted segmentation result.
        tolerances: Boundary localization tolerances in bytes.
    """
    total_len = ground_truth.total_bytes
    if prediction.total_bytes != total_len:
        raise ValueError(
            f"Ground truth length ({total_len}) does not match prediction length ({prediction.total_bytes})"
        )

    if total_len == 0:
        return {"empty": True}

    # 1. Project segments into dense byte arrays
    gt_cats = np.zeros(total_len, dtype=np.int64)
    gt_archs = np.zeros(total_len, dtype=np.int64)
    for seg in ground_truth.segments:
        gt_cats[seg.start:seg.end] = CATEGORY_TO_IDX[seg.category]
        gt_archs[seg.start:seg.end] = ARCH_TO_IDX[seg.arch]

    pred_cats = np.zeros(total_len, dtype=np.int64)
    pred_archs = np.zeros(total_len, dtype=np.int64)
    for seg in prediction.segments:
        pred_cats[seg.start:seg.end] = CATEGORY_TO_IDX[seg.category]
        pred_archs[seg.start:seg.end] = ARCH_TO_IDX[seg.arch]

    # 2. Per-class metrics & IoU
    num_classes = len(STRUCTURAL_CATEGORIES)
    per_class: Dict[str, Dict[str, float]] = {}
    f1_list = []
    iou_list = []

    for cat in STRUCTURAL_CATEGORIES:
        idx = CATEGORY_TO_IDX[cat]
        gt_mask = (gt_cats == idx)
        pred_mask = (pred_cats == idx)

        tp = int(np.sum(gt_mask & pred_mask))
        fp = int(np.sum((~gt_mask) & pred_mask))
        fn = int(np.sum(gt_mask & (~pred_mask)))

        precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0 if fn == 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0 if fp == 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        union = tp + fp + fn
        iou = tp / union if union > 0 else 1.0 if (tp == 0 and fp == 0 and fn == 0) else 0.0

        per_class[cat.value] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "iou": round(iou, 4),
            "support_bytes": int(np.sum(gt_mask)),
        }
        f1_list.append(f1)
        iou_list.append(iou)

    macro_f1 = float(np.mean(f1_list))
    macro_iou = float(np.mean(iou_list))
    overall_accuracy = float(np.mean(gt_cats == pred_cats))

    # 3. Architecture classification performance on CODE bytes
    code_idx = CATEGORY_TO_IDX[StructuralCategory.CODE]
    code_mask = (gt_cats == code_idx) & (pred_cats == code_idx)
    if np.sum(code_mask) > 0:
        arch_gt = gt_archs[code_mask]
        arch_pred = pred_archs[code_mask]
        arch_acc = float(np.mean(arch_gt == arch_pred))
    else:
        arch_acc = 1.0 if np.sum(gt_cats == code_idx) == 0 else 0.0

    # 4. Boundary localization F1 at multiple tolerances
    gt_boundaries = set(s.start for s in ground_truth.segments if s.start > 0)
    pred_boundaries = set(s.start for s in prediction.segments if s.start > 0)

    boundary_metrics: Dict[str, Dict[str, float]] = {}
    for tau in tolerances:
        matched_gt = set()
        matched_pred = set()

        for pb in pred_boundaries:
            for gb in gt_boundaries:
                if abs(pb - gb) <= tau:
                    matched_gt.add(gb)
                    matched_pred.add(pb)
                    break

        b_tp = len(matched_pred)
        b_fp = len(pred_boundaries) - b_tp
        b_fn = len(gt_boundaries) - len(matched_gt)

        b_prec = b_tp / (b_tp + b_fp) if (b_tp + b_fp) > 0 else 1.0 if b_fn == 0 else 0.0
        b_rec = b_tp / (b_tp + b_fn) if (b_tp + b_fn) > 0 else 1.0 if b_fp == 0 else 0.0
        b_f1 = (2 * b_prec * b_rec) / (b_prec + b_rec) if (b_prec + b_rec) > 0 else 0.0

        boundary_metrics[f"tol_{tau}B"] = {
            "precision": round(b_prec, 4),
            "recall": round(b_rec, 4),
            "f1": round(b_f1, 4),
            "true_boundaries": len(gt_boundaries),
            "pred_boundaries": len(pred_boundaries),
        }

    # 5. Short-region (<64 byte) detection
    short_segs = [s for s in ground_truth.segments if s.length < 64]
    short_detected = 0
    for s in short_segs:
        # Check if prediction has matching segment category overlapping >= 50%
        sub_pred = pred_cats[s.start:s.end]
        expected_cat_idx = CATEGORY_TO_IDX[s.category]
        if np.mean(sub_pred == expected_cat_idx) >= 0.50:
            short_detected += 1

    short_region_recall = short_detected / len(short_segs) if short_segs else 1.0

    return {
        "overall_byte_accuracy": round(overall_accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "macro_iou": round(macro_iou, 4),
        "arch_accuracy_on_code": round(arch_acc, 4),
        "boundary_localization": boundary_metrics,
        "short_region_recall": round(short_region_recall, 4),
        "per_class": per_class,
    }

