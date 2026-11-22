"""Unit tests for ELF, PE, and synthetic parsers."""

import pytest
from kethravax.core.types import Architecture, StructuralCategory
from kethravax.data.elf_parser import parse_elf_bytes
from kethravax.data.synthetic import generate_synthetic_stream


def test_synthetic_stream_invariants() -> None:
    data_bytes, res = generate_synthetic_stream("test_synth", target_total_bytes=4096, seed=123)
    assert len(data_bytes) == 4096
    assert res.total_bytes == 4096

    # Verify segmentation invariants
    is_valid, err = res.validate_invariants()
    assert is_valid is True, f"Invariant failure: {err}"

    # Verify exact coverage
    assert res.segments[0].start == 0
    assert res.segments[-1].end == 4096

    for s in res.segments:
        assert s.length > 0
        if s.category == StructuralCategory.CODE:
            assert s.arch != Architecture.NONE


def test_elf_parser_synthetic_header() -> None:
    # Construct a minimal 64-bit Little-Endian ELF header
    # e_ident: 16 bytes (0x7F, 'E', 'L', 'F', 2 (64-bit), 1 (LE), 1 (version), 0...)
    e_ident = bytearray([0x7F, ord('E'), ord('L'), ord('F'), 2, 1, 1, 0] + [0] * 8)
    # e_type=2 (EXEC), e_machine=62 (x86_64), e_version=1, e_entry=0x400000,
    # e_phoff=64, e_shoff=0, e_flags=0, e_ehsize=64, e_phentsize=56, e_phnum=1,
    # e_shentsize=64, e_shnum=0, e_shstrndx=0
    import struct
    hdr = struct.pack("<16sHHIQQQIHHHHHH", e_ident, 2, 62, 1, 0x400000, 64, 0, 0, 64, 56, 1, 64, 0, 0)
    # Add dummy 64 bytes of code payload
    dummy_code = bytes([0x90] * 64)
    elf_data = hdr + dummy_code

    res = parse_elf_bytes(elf_data, "minimal_test.elf")
    assert res.total_bytes == len(elf_data)
    assert res.metadata["arch"] == Architecture.X86_64.value

    is_valid, err = res.validate_invariants()
    assert is_valid is True, f"Invariant error: {err}"

