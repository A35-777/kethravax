"""Synthetic binary stream generator with exact ground truth for multi-class and mixed-architecture streams."""

from __future__ import annotations

import random
import struct
import zlib
from typing import Dict, List, Optional, Tuple

from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.utils.entropy import calculate_byte_diagnostics


# Architecture-specific code pattern templates
X86_64_SNIPPETS = [
    # Function prologue & stack alloc
    bytes([0x55, 0x48, 0x89, 0xE5, 0x48, 0x83, 0xEC, 0x20]),
    # Common operations: mov, add, test, jz
    bytes([0x48, 0x89, 0x7D, 0xE8, 0x48, 0x8B, 0x45, 0xE8, 0x48, 0x83, 0xC0, 0x08]),
    bytes([0x48, 0x85, 0xC0, 0x74, 0x05, 0xE8, 0x20, 0x00, 0x00, 0x00]),
    bytes([0x8B, 0x45, 0xFC, 0x83, 0xC0, 0x01, 0x89, 0x45, 0xFC, 0xEB, 0x02]),
    # Epilogue: leave, ret
    bytes([0x48, 0x83, 0xC4, 0x20, 0x5D, 0xC3]),
    bytes([0xC9, 0xC3]),
]

X86_32_SNIPPETS = [
    bytes([0x55, 0x89, 0xE5, 0x83, 0xEC, 0x18]),
    bytes([0x8B, 0x45, 0x08, 0x03, 0x45, 0x0C, 0x89, 0x45, 0xFC]),
    bytes([0x83, 0x7D, 0xFC, 0x00, 0x7E, 0x0A, 0x8B, 0x45, 0xFC, 0x48]),
    bytes([0x89, 0xEC, 0x5D, 0xC3]),
]

ARM32_ARM_SNIPPETS = [
    # stmfd sp!, {fp, lr} (0xe92d4800 in LE)
    bytes([0x00, 0x48, 0x2D, 0xE9, 0x04, 0xB0, 0x8D, 0xE2]),
    # add r0, r1, r2
    bytes([0x02, 0x00, 0x81, 0xE0, 0x00, 0x00, 0x50, 0xE3]),
    # ldr r3, [r11, #-8]
    bytes([0x08, 0x30, 0x1B, 0xE5, 0x01, 0x30, 0x83, 0xE2]),
    # ldmfd sp!, {fp, pc}
    bytes([0x00, 0x88, 0xBD, 0xE8]),
]

ARM32_THUMB_SNIPPETS = [
    # push {r4, r7, lr}
    bytes([0x90, 0xB5, 0x02, 0xAF]),
    # sub sp, #12
    bytes([0x83, 0xB0, 0x03, 0x46]),
    # adds r0, #1; cmp r0, #10; bne
    bytes([0x01, 0x30, 0x0A, 0x28, 0xD1, 0xD1]),
    # pop {r4, r7, pc}
    bytes([0x90, 0xBD]),
]

AARCH64_SNIPPETS = [
    # stp x29, x30, [sp, #-32]!
    bytes([0xFD, 0x7B, 0xBE, 0xA9, 0xFD, 0x03, 0x00, 0x91]),
    # str w0, [x29, #28]; ldr w0, [x29, #28]
    bytes([0xE0, 0x0F, 0x00, 0xB9, 0xE0, 0x0F, 0x40, 0xB9]),
    # add w0, w0, #1
    bytes([0x00, 0x04, 0x00, 0x11, 0x7F, 0x00, 0x00, 0x71]),
    # ldp x29, x30, [sp], #32; ret
    bytes([0xFD, 0x7B, 0xC2, 0xA8, 0xC0, 0x03, 0x5F, 0xD6]),
]

MIPS32_SNIPPETS = [
    # addiu sp, sp, -32; sw ra, 28(sp); sw fp, 24(sp)
    bytes([0x27, 0xBD, 0xFF, 0xE0, 0xAF, 0xBF, 0x00, 0x1C, 0xAF, 0xBE, 0x00, 0x18]),
    # move fp, sp; lw v0, 24(fp); addiu v0, v0, 1
    bytes([0x03, 0xA0, 0xF0, 0x25, 0x8F, 0xC2, 0x00, 0x18, 0x24, 0x42, 0x00, 0x01]),
    # jr ra; nop (delay slot)
    bytes([0x03, 0xE0, 0x00, 0x08, 0x00, 0x00, 0x00, 0x00]),
]

RISCV_SNIPPETS = [
    # addi sp, sp, -32; sd ra, 24(sp); sd s0, 16(sp)
    bytes([0x13, 0x01, 0x01, 0xFE, 0x23, 0x3C, 0x11, 0x01, 0x23, 0x38, 0x81, 0x01]),
    # addi s0, sp, 32; lw a0, -20(s0); addi a0, a0, 1
    bytes([0x13, 0x04, 0x01, 0x02, 0x03, 0x25, 0xC4, 0xFE, 0x13, 0x05, 0x15, 0x00]),
    # ret (jalr x0, 0(ra))
    bytes([0x67, 0x80, 0x00, 0x00]),
]

SAMPLE_STRINGS = [
    "Error: failed to initialize cryptographic subsystem\x00",
    "Usage: ./kethravax-core [OPTIONS] <input_stream>\x00",
    "HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\n\r\n\x00",
    "/usr/lib/x86_64-linux-gnu/libpthread.so.0\x00",
    "Invalid memory access at offset 0x%08X\x00",
    "FATAL EXCEPTION: Stack canary corrupted in thread 0x%lx\x00",
    "Initializing hardware DMA channel %d with buffer size %u\x00",
    "Certificate signature verification succeeded for %s\x00",
    "libgcc_s.so.1\x00_Unwind_Resume\x00__gcc_personality_v0\x00",
    "Starting system bus daemon: dbus-daemon\x00",
]


def generate_code_block(arch: Architecture, target_len: int, rng: random.Random) -> bytes:
    """Generate a pseudo-realistic code sequence for a specified architecture."""
    snippets_map = {
        Architecture.X86_64: X86_64_SNIPPETS,
        Architecture.X86_32: X86_32_SNIPPETS,
        Architecture.ARM32_ARM: ARM32_ARM_SNIPPETS,
        Architecture.ARM32_THUMB: ARM32_THUMB_SNIPPETS,
        Architecture.AARCH64: AARCH64_SNIPPETS,
        Architecture.MIPS32: MIPS32_SNIPPETS,
        Architecture.RISCV: RISCV_SNIPPETS,
    }
    snippets = snippets_map.get(arch, X86_64_SNIPPETS)
    buf = bytearray()
    while len(buf) < target_len:
        s = rng.choice(snippets)
        buf.extend(s)
        # Occasionally insert small randomized operands or offsets
        if rng.random() < 0.3:
            rem = target_len - len(buf)
            if rem > 0:
                buf.extend(rng.randbytes(min(4, rem)))

    return bytes(buf[:target_len])


def generate_string_pool(target_len: int, rng: random.Random) -> bytes:
    """Generate a realistic null-delimited ASCII string pool."""
    buf = bytearray()
    while len(buf) < target_len:
        s = rng.choice(SAMPLE_STRINGS).encode("utf-8")
        buf.extend(s)
    return bytes(buf[:target_len])


def generate_table_block(target_len: int, rng: random.Random) -> bytes:
    """Generate a realistic pointer table / jump table block."""
    buf = bytearray()
    base_addr = rng.choice([0x00401000, 0x00007FF71000, 0x08048000])
    is_64 = base_addr > 0xFFFFFFFF
    entry_size = 8 if is_64 else 4
    num_entries = max(1, target_len // entry_size)

    curr_addr = base_addr
    for _ in range(num_entries):
        curr_addr += rng.choice([16, 32, 48, 64, 128])
        if is_64:
            buf.extend(struct.pack("<Q", curr_addr))
        else:
            buf.extend(struct.pack("<I", curr_addr))

    while len(buf) < target_len:
        buf.append(0)

    return bytes(buf[:target_len])


def generate_padding_block(target_len: int, rng: random.Random) -> bytes:
    """Generate alignment padding (nulls, NOPs, or int3)."""
    pad_byte = rng.choice([0x00, 0x90, 0xCC])
    return bytes([pad_byte] * target_len)


def generate_compressed_block(target_len: int, rng: random.Random) -> bytes:
    """Generate high-entropy compressed/opaque payload using zlib."""
    raw_source = rng.randbytes(target_len * 2)
    compressed = zlib.compress(raw_source, level=rng.choice([1, 6, 9]))
    if len(compressed) >= target_len:
        return compressed[:target_len]
    # Pad remainder with pseudo-random high entropy bytes
    return compressed + rng.randbytes(target_len - len(compressed))


def generate_raw_data_block(target_len: int, rng: random.Random) -> bytes:
    """Generate structured constant non-string raw data."""
    buf = bytearray()
    for _ in range(max(1, target_len // 4)):
        val = rng.randint(0, 0x0000FFFF)
        buf.extend(struct.pack("<I", val))
    while len(buf) < target_len:
        buf.append(rng.randint(0, 255))
    return bytes(buf[:target_len])


def generate_synthetic_stream(
    stream_id: str,
    target_total_bytes: int = 16384,
    seed: int = 42,
    include_mixed_arch: bool = True,
) -> Tuple[bytes, SegmentationResult]:
    """Generate a multi-class synthetic binary stream with exact ground truth.
    
    Guarantees:
    - Non-overlapping contiguity.
    - Total byte coverage from 0 to target_total_bytes.
    - Exact byte boundaries.
    """
    rng = random.Random(seed)
    stream_buf = bytearray()
    segments: List[Segment] = []

    arch_candidates = [
        Architecture.X86_64,
        Architecture.X86_32,
        Architecture.ARM32_ARM,
        Architecture.ARM32_THUMB,
        Architecture.AARCH64,
        Architecture.MIPS32,
        Architecture.RISCV,
    ]

    current_offset = 0
    while current_offset < target_total_bytes:
        remaining = target_total_bytes - current_offset
        # Choose segment length between 64 and 2048 bytes (or remainder)
        seg_len = min(remaining, rng.randint(64, min(1024, max(64, remaining))))
        
        # Select structural category
        choices = [
            StructuralCategory.CODE,
            StructuralCategory.DATA_STRING,
            StructuralCategory.DATA_TABLE,
            StructuralCategory.DATA_RAW,
            StructuralCategory.PADDING,
            StructuralCategory.COMPRESSED_OPAQUE,
        ]
        cat = rng.choice(choices)

        if cat == StructuralCategory.CODE:
            arch = rng.choice(arch_candidates) if include_mixed_arch else Architecture.X86_64
            chunk_bytes = generate_code_block(arch, seg_len, rng)
        elif cat == StructuralCategory.DATA_STRING:
            arch = Architecture.NONE
            chunk_bytes = generate_string_pool(seg_len, rng)
        elif cat == StructuralCategory.DATA_TABLE:
            arch = Architecture.NONE
            chunk_bytes = generate_table_block(seg_len, rng)
        elif cat == StructuralCategory.PADDING:
            arch = Architecture.NONE
            chunk_bytes = generate_padding_block(seg_len, rng)
        elif cat == StructuralCategory.COMPRESSED_OPAQUE:
            arch = Architecture.NONE
            chunk_bytes = generate_compressed_block(seg_len, rng)
        else:
            arch = Architecture.NONE
            chunk_bytes = generate_raw_data_block(seg_len, rng)

        stream_buf.extend(chunk_bytes)
        seg_end = current_offset + len(chunk_bytes)

        diag = calculate_byte_diagnostics(chunk_bytes)
        segments.append(
            Segment(
                start=current_offset,
                end=seg_end,
                category=cat,
                arch=arch,
                confidence=1.0,
                diagnostics={"synthetic": True, "seed": seed, **diag},
            )
        )
        current_offset = seg_end

    # Merge consecutive identical segments if any
    merged: List[Segment] = []
    for s in segments:
        if not merged:
            merged.append(s)
        else:
            last = merged[-1]
            if last.category == s.category and last.arch == s.arch:
                merged[-1] = Segment(
                    start=last.start,
                    end=s.end,
                    category=last.category,
                    arch=last.arch,
                    confidence=1.0,
                    diagnostics={**last.diagnostics, "merged": True},
                )
            else:
                merged.append(s)

    result = SegmentationResult(
        stream_id=stream_id,
        total_bytes=len(stream_buf),
        segments=merged,
        metadata={"synthetic": True, "seed": seed, "mixed_arch": include_mixed_arch},
    )

    is_valid, err = result.validate_invariants()
    if not is_valid:
        raise ValueError(f"Synthetic generation invariant failure: {err}")

    return bytes(stream_buf), result
