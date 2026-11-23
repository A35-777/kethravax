"""KETHRAVAX: Precision structural byte segmentation & ISA discovery for raw binary streams."""

from kethravax.core.taxonomy import (
    ARCH_COLORS,
    ARCH_TO_IDX,
    ARCHITECTURES,
    CATEGORY_COLORS,
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
from kethravax.inference.engine import BinarySegmenter

__version__ = "0.1.0"
__author__ = "Arin Goel"

__all__ = [
    "BinarySegmenter",
    "Segment",
    "SegmentationResult",
    "StructuralCategory",
    "Architecture",
    "STRUCTURAL_CATEGORIES",
    "CATEGORY_TO_IDX",
    "IDX_TO_CATEGORY",
    "ARCHITECTURES",
    "ARCH_TO_IDX",
    "IDX_TO_ARCH",
    "CATEGORY_COLORS",
    "ARCH_COLORS",
    "__version__",
]

