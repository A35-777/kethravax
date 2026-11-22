"""PE (Portable Executable) ground-truth metadata and segment extractor."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple
import pefile

from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.utils.entropy import calculate_byte_diagnostics


def parse_pe_architecture(pe: pefile.PE) -> Architecture:
    """Map PE machine type to Architecture enum."""
    machine = getattr(pe.FILE_HEADER, "Machine", 0)
    # IMAGE_FILE_MACHINE_AMD64 = 0x8664
    if machine == 0x8664:
        return Architecture.X86_64
    # IMAGE_FILE_MACHINE_I386 = 0x014C
    elif machine == 0x014C:
        return Architecture.X86_32
    # IMAGE_FILE_MACHINE_ARMNT = 0x01C4 (Thumb-2)
    elif machine == 0x01C4:
        return Architecture.ARM32_THUMB
    # IMAGE_FILE_MACHINE_ARM64 = 0xAA64
    elif machine == 0xAA64:
        return Architecture.AARCH64
    elif machine == 0x0200:  # IA64
        return Architecture.ARCH_UNKNOWN
    return Architecture.ARCH_UNKNOWN


def extract_pe_ground_truth(file_path: str) -> SegmentationResult:
    """Extract fine-grained structural ground-truth segments from a valid PE file.
    
    Adheres strictly to the task guidelines:
    - Preserves exact byte offsets [0, file_size) without gaps or overlaps.
    - Accurately categorizes headers, code, string pools, tables, and alignment padding.
    """
    file_size = os.path.getsize(file_path)
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    pe = pefile.PE(data=file_bytes, fast_load=False)
    arch = parse_pe_architecture(pe)

    raw_segments: List[Segment] = []

    # 1. Header region: From offset 0 up to the start of the first section
    first_section_offset = file_size
    for section in pe.sections:
        offset = section.PointerToRawData
        if offset > 0 and offset < first_section_offset:
            first_section_offset = offset

    if first_section_offset > 0:
        header_bytes = file_bytes[0:first_section_offset]
        raw_segments.append(
            Segment(
                start=0,
                end=first_section_offset,
                category=StructuralCategory.DATA_RAW,
                arch=Architecture.NONE,
                confidence=1.0,
                diagnostics={"region": "PE_HEADER", **calculate_byte_diagnostics(header_bytes)},
            )
        )

    # 2. Iterate through sections ordered by raw data pointer
    sections = sorted(pe.sections, key=lambda s: s.PointerToRawData)
    prev_end = first_section_offset

    for section in sections:
        sec_name = section.Name.decode("utf-8", errors="ignore").rstrip("\x00")
        sec_offset = section.PointerToRawData
        sec_size = section.SizeOfRawData
        virt_size = section.Misc_VirtualSize

        # Check for gap between previous section and current section
        if sec_offset > prev_end:
            gap_bytes = file_bytes[prev_end:sec_offset]
            raw_segments.append(
                Segment(
                    start=prev_end,
                    end=sec_offset,
                    category=StructuralCategory.PADDING,
                    arch=Architecture.NONE,
                    confidence=1.0,
                    diagnostics={"region": "INTER_SECTION_GAP", **calculate_byte_diagnostics(gap_bytes)},
                )
            )

        if sec_size == 0 or sec_offset >= file_size:
            prev_end = max(prev_end, sec_offset)
            continue

        sec_end = min(file_size, sec_offset + sec_size)
        sec_bytes = file_bytes[sec_offset:sec_end]

        # Determine category based on section characteristics and name
        chars = section.Characteristics
        is_code = bool(chars & 0x00000020) or (sec_name.lower() in (".text", "code"))
        
        # Check if actual content has padding at the tail (file alignment padding)
        # When SizeOfRawData > Misc_VirtualSize, the remainder is typically null/alignment
        active_size = min(sec_size, virt_size) if (0 < virt_size < sec_size) else sec_size
        active_end = sec_offset + active_size

        if is_code:
            code_bytes = file_bytes[sec_offset:active_end]
            raw_segments.append(
                Segment(
                    start=sec_offset,
                    end=active_end,
                    category=StructuralCategory.CODE,
                    arch=arch,
                    confidence=1.0,
                    diagnostics={"section": sec_name, **calculate_byte_diagnostics(code_bytes)},
                )
            )
            if active_end < sec_end:
                pad_bytes = file_bytes[active_end:sec_end]
                raw_segments.append(
                    Segment(
                        start=active_end,
                        end=sec_end,
                        category=StructuralCategory.PADDING,
                        arch=Architecture.NONE,
                        confidence=1.0,
                        diagnostics={"section": sec_name + "_PAD", **calculate_byte_diagnostics(pad_bytes)},
                    )
                )
        elif sec_name.lower() in (".rdata", ".idata", ".pdata", ".reloc", ".got"):
            # Check if this is a table or string pool
            diag = calculate_byte_diagnostics(sec_bytes)
            if diag["printable_ratio"] > 0.65:
                cat = StructuralCategory.DATA_STRING
            elif sec_name.lower() in (".pdata", ".reloc", ".idata"):
                cat = StructuralCategory.DATA_TABLE
            else:
                cat = StructuralCategory.DATA_TABLE if diag["null_ratio"] > 0.35 else StructuralCategory.DATA_RAW

            raw_segments.append(
                Segment(
                    start=sec_offset,
                    end=sec_end,
                    category=cat,
                    arch=Architecture.NONE,
                    confidence=1.0,
                    diagnostics={"section": sec_name, **diag},
                )
            )
        else:
            diag = calculate_byte_diagnostics(sec_bytes)
            if diag["printable_ratio"] > 0.70:
                cat = StructuralCategory.DATA_STRING
            elif diag["entropy"] >= 7.2:
                cat = StructuralCategory.COMPRESSED_OPAQUE
            else:
                cat = StructuralCategory.DATA_RAW

            raw_segments.append(
                Segment(
                    start=sec_offset,
                    end=sec_end,
                    category=cat,
                    arch=Architecture.NONE,
                    confidence=1.0,
                    diagnostics={"section": sec_name, **diag},
                )
            )

        prev_end = sec_end

    # 3. Check for any overlay or trailing data after the last section
    if prev_end < file_size:
        overlay_bytes = file_bytes[prev_end:file_size]
        diag = calculate_byte_diagnostics(overlay_bytes)
        cat = StructuralCategory.COMPRESSED_OPAQUE if diag["entropy"] >= 7.2 else StructuralCategory.DATA_RAW
        raw_segments.append(
            Segment(
                start=prev_end,
                end=file_size,
                category=cat,
                arch=Architecture.NONE,
                confidence=1.0,
                diagnostics={"region": "OVERLAY", **diag},
            )
        )

    # Coalesce adjacent identical segments and validate
    merged_segments: List[Segment] = []
    for s in raw_segments:
        if not merged_segments:
            merged_segments.append(s)
        else:
            last = merged_segments[-1]
            if last.category == s.category and last.arch == s.arch:
                merged_segments[-1] = Segment(
                    start=last.start,
                    end=s.end,
                    category=last.category,
                    arch=last.arch,
                    confidence=min(last.confidence, s.confidence),
                    diagnostics={**last.diagnostics, "merged_with": s.diagnostics},
                )
            else:
                merged_segments.append(s)

    result = SegmentationResult(
        stream_id=os.path.basename(file_path),
        total_bytes=file_size,
        segments=merged_segments,
        metadata={
            "format": "PE",
            "arch": arch.value,
            "section_count": len(pe.sections),
            "file_path": file_path,
        },
    )

    is_valid, err = result.validate_invariants()
    if not is_valid:
        raise ValueError(f"PE ground-truth extraction invariant failure: {err}")

    return result

