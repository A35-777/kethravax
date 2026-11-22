"""Kethravax Data Module."""

from kethravax.data.dataset import BinaryStreamDataset
from kethravax.data.elf_parser import extract_elf_ground_truth, parse_elf_bytes
from kethravax.data.pe_parser import extract_pe_ground_truth, parse_pe_architecture
from kethravax.data.synthetic import generate_synthetic_stream
from kethravax.data.validation import audit_dataset_splits, compute_stream_hash

__all__ = [
    "BinaryStreamDataset",
    "extract_pe_ground_truth",
    "parse_pe_architecture",
    "extract_elf_ground_truth",
    "parse_elf_bytes",
    "generate_synthetic_stream",
    "compute_stream_hash",
    "audit_dataset_splits",
]

