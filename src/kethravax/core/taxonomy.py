"""Taxonomy mappings, color representations, and indexing utilities."""

from typing import Dict, List, Tuple
from kethravax.core.types import Architecture, StructuralCategory

# Integer mapping for categorical modeling
STRUCTURAL_CATEGORIES: List[StructuralCategory] = [
    StructuralCategory.CODE,
    StructuralCategory.DATA_STRING,
    StructuralCategory.DATA_TABLE,
    StructuralCategory.DATA_RAW,
    StructuralCategory.PADDING,
    StructuralCategory.COMPRESSED_OPAQUE,
    StructuralCategory.UNKNOWN_AMBIGUOUS,
]

CATEGORY_TO_IDX: Dict[StructuralCategory, int] = {
    cat: i for i, cat in enumerate(STRUCTURAL_CATEGORIES)
}

IDX_TO_CATEGORY: Dict[int, StructuralCategory] = {
    i: cat for i, cat in enumerate(STRUCTURAL_CATEGORIES)
}

ARCHITECTURES: List[Architecture] = [
    Architecture.NONE,
    Architecture.X86_64,
    Architecture.X86_32,
    Architecture.ARM32_ARM,
    Architecture.ARM32_THUMB,
    Architecture.AARCH64,
    Architecture.MIPS32,
    Architecture.RISCV,
    Architecture.ARCH_UNKNOWN,
]

ARCH_TO_IDX: Dict[Architecture, int] = {
    arch: i for i, arch in enumerate(ARCHITECTURES)
}

IDX_TO_ARCH: Dict[int, Architecture] = {
    i: arch for i, arch in enumerate(ARCHITECTURES)
}

# Terminal ANSI & Hex RGB color palettes for UI / CLI
CATEGORY_COLORS: Dict[StructuralCategory, Dict[str, str]] = {
    StructuralCategory.CODE: {
        "hex": "#00F0FF",
        "ansi": "\033[96m",
        "name": "Cyan",
        "label": "Code",
    },
    StructuralCategory.DATA_STRING: {
        "hex": "#F59E0B",
        "ansi": "\033[93m",
        "name": "Amber",
        "label": "String Pool",
    },
    StructuralCategory.DATA_TABLE: {
        "hex": "#10B981",
        "ansi": "\033[92m",
        "name": "Emerald",
        "label": "Jump / Data Table",
    },
    StructuralCategory.DATA_RAW: {
        "hex": "#3B82F6",
        "ansi": "\033[94m",
        "name": "Blue",
        "label": "Raw Constant Data",
    },
    StructuralCategory.PADDING: {
        "hex": "#64748B",
        "ansi": "\033[90m",
        "name": "Slate",
        "label": "Alignment / Padding",
    },
    StructuralCategory.COMPRESSED_OPAQUE: {
        "hex": "#8B5CF6",
        "ansi": "\033[95m",
        "name": "Purple",
        "label": "Compressed / Opaque",
    },
    StructuralCategory.UNKNOWN_AMBIGUOUS: {
        "hex": "#EF4444",
        "ansi": "\033[91m",
        "name": "Crimson",
        "label": "Unknown / Ambiguous",
    },
}

ARCH_COLORS: Dict[Architecture, str] = {
    Architecture.NONE: "#64748B",
    Architecture.X86_64: "#06B6D4",
    Architecture.X86_32: "#0284C7",
    Architecture.ARM32_ARM: "#10B981",
    Architecture.ARM32_THUMB: "#059669",
    Architecture.AARCH64: "#6366F1",
    Architecture.MIPS32: "#EC4899",
    Architecture.RISCV: "#F97316",
    Architecture.ARCH_UNKNOWN: "#94A3B8",
}

ANSI_RESET: str = "\033[0m"

