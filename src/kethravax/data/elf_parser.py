"""Pure-Python ELF (Executable and Linkable Format) parser and ground-truth extractor.

Supports ELF32 and ELF64, Little-Endian and Big-Endian, architecture discovery,
and fine-grained section and mapping symbol segmentation.
"""

from __future__ import annotations

import os
import struct
from typing import Any, Dict, List, Optional, Tuple

from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.utils.entropy import calculate_byte_diagnostics

# ELF Machine types
EM_386 = 3
EM_MIPS = 8
EM_ARM = 40
EM_X86_64 = 62
EM_AARCH64 = 183
EM_RISCV = 243

# Section types
SHT_NULL = 0
SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_STRTAB = 3
SHT_RELA = 4
SHT_HASH = 5
SHT_DYNAMIC = 6
SHT_NOTE = 7
SHT_NOBITS = 8
SHT_REL = 9
SHT_SHLIB = 10
SHT_DYNSYM = 11

# Section flags
SHF_WRITE = 0x1
SHF_ALLOC = 0x2
SHF_EXECINSTR = 0x4


def map_elf_machine_to_arch(machine: int) -> Architecture:
    """Map ELF e_machine code to Architecture enum."""
    if machine == EM_X86_64:
        return Architecture.X86_64
    elif machine == EM_386:
        return Architecture.X86_32
    elif machine == EM_ARM:
        return Architecture.ARM32_ARM
    elif machine == EM_AARCH64:
        return Architecture.AARCH64
    elif machine == EM_MIPS:
        return Architecture.MIPS32
    elif machine == EM_RISCV:
        return Architecture.RISCV
    return Architecture.ARCH_UNKNOWN


def parse_elf_bytes(data: bytes, file_name: str = "stream.elf") -> SegmentationResult:
    """Parse raw ELF bytes into dense ground-truth segments."""
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ValueError("Not a valid ELF binary header")

    ei_class = data[4]  # 1 = 32-bit, 2 = 64-bit
    ei_data = data[5]   # 1 = Little Endian, 2 = Big Endian
    endian_char = "<" if ei_data == 1 else ">"

    is_64 = (ei_class == 2)
    fmt_hdr = endian_char + ("16sHHIQQQIHHHHHH" if is_64 else "16sHHIIIIIHHHHHH")
    hdr_size = 64 if is_64 else 52

    if len(data) < hdr_size:
        raise ValueError("ELF truncated before full header")

    unpacked = struct.unpack(fmt_hdr, data[:hdr_size])
    e_type = unpacked[1]
    e_machine = unpacked[2]
    e_version = unpacked[3]
    e_entry = unpacked[4]
    e_phoff = unpacked[5]
    e_shoff = unpacked[6]
    e_flags = unpacked[7]
    e_ehsize = unpacked[8]
    e_phentsize = unpacked[9]
    e_phnum = unpacked[10]
    e_shentsize = unpacked[11]
    e_shnum = unpacked[12]
    e_shstrndx = unpacked[13]

    base_arch = map_elf_machine_to_arch(e_machine)

    # Read section string table if present
    shstrtab = b""
    if e_shoff > 0 and e_shnum > 0 and e_shstrndx < e_shnum:
        sh_offset = e_shoff + (e_shstrndx * e_shentsize)
        fmt_sh = endian_char + ("IIQQQQIIQQ" if is_64 else "IIIIIIIIII")
        if sh_offset + e_shentsize <= len(data):
            sh_unpacked = struct.unpack(fmt_sh, data[sh_offset : sh_offset + e_shentsize])
            strtab_offset = sh_unpacked[4]
            strtab_size = sh_unpacked[5]
            if strtab_offset + strtab_size <= len(data):
                shstrtab = data[strtab_offset : strtab_offset + strtab_size]

    def get_section_name(name_idx: int) -> str:
        if not shstrtab or name_idx >= len(shstrtab):
            return ""
        end = shstrtab.find(b"\x00", name_idx)
        if end == -1:
            end = len(shstrtab)
        return shstrtab[name_idx:end].decode("utf-8", errors="ignore")

    # Parse all sections
    sections: List[Dict[str, Any]] = []
    fmt_sh = endian_char + ("IIQQQQIIQQ" if is_64 else "IIIIIIIIII")
    for i in range(e_shnum):
        sh_offset = e_shoff + (i * e_shentsize)
        if sh_offset + e_shentsize > len(data):
            break
        sh = struct.unpack(fmt_sh, data[sh_offset : sh_offset + e_shentsize])
        sh_name_idx = sh[0]
        sh_type = sh[1]
        sh_flags = sh[2]
        sh_addr = sh[3]
        sh_offset_val = sh[4]
        sh_size = sh[5]
        name = get_section_name(sh_name_idx)

        # SHT_NOBITS (like .bss) does not occupy bytes in the file
        if sh_type == SHT_NOBITS or sh_size == 0:
            continue

        if sh_offset_val < len(data):
            sections.append({
                "index": i,
                "name": name,
                "type": sh_type,
                "flags": sh_flags,
                "offset": sh_offset_val,
                "size": min(sh_size, len(data) - sh_offset_val),
            })

    # Sort sections by file offset
    sections = sorted(sections, key=lambda s: s["offset"])

    raw_segments: List[Segment] = []
    prev_end = 0

    # ELF Header segment
    header_end = min(len(data), hdr_size)
    if sections and sections[0]["offset"] > header_end:
        header_end = sections[0]["offset"]

    raw_segments.append(
        Segment(
            start=0,
            end=header_end,
            category=StructuralCategory.DATA_RAW,
            arch=Architecture.NONE,
            confidence=1.0,
            diagnostics={"region": "ELF_HEADER", **calculate_byte_diagnostics(data[0:header_end])},
        )
    )
    prev_end = header_end

    for sec in sections:
        sec_offset = sec["offset"]
        sec_size = sec["size"]
        sec_end = min(len(data), sec_offset + sec_size)

        if sec_offset > prev_end:
            # Alignment gap
            gap_bytes = data[prev_end:sec_offset]
            raw_segments.append(
                Segment(
                    start=prev_end,
                    end=sec_offset,
                    category=StructuralCategory.PADDING,
                    arch=Architecture.NONE,
                    confidence=1.0,
                    diagnostics={"region": "ELF_GAP", **calculate_byte_diagnostics(gap_bytes)},
                )
            )

        sec_bytes = data[sec_offset:sec_end]
        diag = calculate_byte_diagnostics(sec_bytes)
        name = sec["name"]
        flags = sec["flags"]
        stype = sec["type"]

        if bool(flags & SHF_EXECINSTR) or name in (".text", ".init", ".fini"):
            cat = StructuralCategory.CODE
            arch = base_arch
        elif stype == SHT_STRTAB or name.startswith((".rodata.str", ".shstrtab", ".strtab", ".dynstr")):
            cat = StructuralCategory.DATA_STRING
            arch = Architecture.NONE
        elif stype in (SHT_RELA, SHT_REL, SHT_DYNAMIC) or name in (".got", ".got.plt", ".init_array", ".fini_array"):
            cat = StructuralCategory.DATA_TABLE
            arch = Architecture.NONE
        elif diag["printable_ratio"] > 0.70:
            cat = StructuralCategory.DATA_STRING
            arch = Architecture.NONE
        elif diag["entropy"] >= 7.2:
            cat = StructuralCategory.COMPRESSED_OPAQUE
            arch = Architecture.NONE
        else:
            cat = StructuralCategory.DATA_RAW
            arch = Architecture.NONE

        raw_segments.append(
            Segment(
                start=sec_offset,
                end=sec_end,
                category=cat,
                arch=arch,
                confidence=1.0,
                diagnostics={"section": name, **diag},
            )
        )
        prev_end = sec_end

    # Trailing bytes (e.g. section header table itself at the end of the file)
    if prev_end < len(data):
        tail_bytes = data[prev_end:]
        raw_segments.append(
            Segment(
                start=prev_end,
                end=len(data),
                category=StructuralCategory.DATA_TABLE if e_shoff >= prev_end else StructuralCategory.DATA_RAW,
                arch=Architecture.NONE,
                confidence=1.0,
                diagnostics={"region": "ELF_TAIL", **calculate_byte_diagnostics(tail_bytes)},
            )
        )

    # Coalesce adjacent segments
    merged: List[Segment] = []
    for s in raw_segments:
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
                    confidence=min(last.confidence, s.confidence),
                    diagnostics={**last.diagnostics, "merged_with": s.diagnostics},
                )
            else:
                merged.append(s)

    result = SegmentationResult(
        stream_id=file_name,
        total_bytes=len(data),
        segments=merged,
        metadata={
            "format": "ELF",
            "is_64": is_64,
            "machine": e_machine,
            "arch": base_arch.value,
        },
    )

    is_valid, err = result.validate_invariants()
    if not is_valid:
        raise ValueError(f"ELF extraction invariant failure: {err}")

    return result


def extract_elf_ground_truth(file_path: str) -> SegmentationResult:
    """Read ELF file from disk and parse ground-truth segments."""
    with open(file_path, "rb") as f:
        data = f.read()
    return parse_elf_bytes(data, file_name=os.path.basename(file_path))

