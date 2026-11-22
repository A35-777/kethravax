# Ground-Truth Annotation Guidelines & Grounding Rules

**Document Version:** 1.0.0  
**Project:** KETHRAVAX  
**Classification:** Data Engineering Standards  
**Date:** 2026-11-22  

---

## 1. Principles of Ground-Truth Extraction

Ground-truth labels must be derived from verifiable structural metadata, linker specifications, debug symbols, and controlled source compilations.

**Metadata is treated as evidence, not infallible truth.**  
For example:
- An ELF `.text` section contains primarily executable code, but compilers frequently interleave jump tables, literal pools, and alignment padding directly within `.text`.
- Simply assigning the label `CODE` to every byte inside `.text` creates noisy, incorrect ground truth.
- True ground-truth extraction must parse symbol tables, mapping symbols, relocation records, and disassembly validation.

---

## 2. ELF Annotation Protocol

When parsing ELF binaries (Linux, Android, OpenWrt, firmware builds):

### 2.1 Code vs Data Disentanglement inside `.text`
1. **ARM Mapping Symbols:**
   In ARM and Thumb binaries, compilers emit standardized mapping symbols in the symbol table (`.symtab`):
   - `$a`: Marks the beginning of ARM state code.
   - `$t`: Marks the beginning of Thumb state code.
   - `$d`: Marks the beginning of a data item (literal pool, jump table, alignment).
   *Rule:* Any byte range in `.text` bounded by `$d` must be annotated as `DATA_TABLE`, `DATA_RAW`, or `PADDING`, **never** `CODE`.
2. **Function Symbol Spans:**
   - Extract function symbols (`STT_FUNC`). Bytes inside $[st\_value, st\_value + st\_size)$ with no conflicting `$d` symbol are annotated as `CODE` with the binary's target architecture.
3. **Inter-Function Padding:**
   - Byte gaps between consecutive function symbols or following the final `ret`/`epilogue` up to the section alignment boundary must be inspected:
     - If bytes are all `0x00`, `0x90`, or `0xCC`, label as `PADDING`.

### 2.2 Section-Level Ground Truth
1. **String Pools:**
   - `.rodata.str1.1`, `.rodata.str1.4`, `.shstrtab`, `.strtab`, `.dynstr`:
     - Inspect byte content: if >85% printable ASCII/UTF-8 with null delimiters, label as `DATA_STRING`.
2. **Jump Tables & Pointer Arrays:**
   - `.got`, `.got.plt`, `.init_array`, `.fini_array`, `.data.rel.ro`:
     - Label as `DATA_TABLE`.
3. **Constant Data:**
   - Non-string `.rodata` chunks:
     - Label as `DATA_RAW`.
4. **BSS Sections (`.bss`):**
   - *Critical Rule:* `.bss` occupies virtual memory space (`SHT_NOBITS`), but occupies **zero bytes** in the file on disk (`sh_size > 0`, but no file content).
   - *Rule:* `.bss` must **not** be assigned byte offsets in file-stream ground truth.

---

## 3. PE & Mach-O Annotation Protocol

### 3.1 Windows Portable Executable (PE)
- Extract section headers: `.text`, `.rdata`, `.data`, `.pdata`, `.rsrc`, `.reloc`.
- Parse Export Table, Import Address Table (IAT), Exception Directory (`.pdata` function runtime tables for x64).
- Bytes within `.pdata` and IAT are labeled `DATA_TABLE`.
- Bytes within `.rdata` containing ASCII/UTF-16 resource strings are labeled `DATA_STRING`.
- Inter-section padding bytes (e.g. padding to `FileAlignment` boundary) are labeled `PADDING`.

### 3.2 macOS Mach-O
- Parse segment commands (`LC_SEGMENT_64`) and section structures (`__TEXT,__text`, `__TEXT,__cstring`, `__DATA,__const`).
- `__cstring` is labeled `DATA_STRING`.
- `__la_symbol_ptr`, `__nl_symbol_ptr` are labeled `DATA_TABLE`.

---

## 4. Synthetic Mixture Ground Truth Protocol

To supplement real-world compiled binaries and rigorously evaluate **mixed-architecture streams**, **headerless slices**, and **boundary localization**, a deterministic synthetic mixture pipeline is established:

1. **Constituent Chunks:** Real compiled chunks (code from x86, ARM, AArch64, MIPS, RISC-V, verified string tables, verified pointer arrays, padding sequences, zlib compressed blobs) are extracted from verified builds.
2. **Deterministic Splicing:** Chunks are spliced contiguously at pseudo-random lengths ($L \in [32, 8192]$ bytes).
3. **Exact Ground-Truth Manifest:** Splicing records exact byte start/end boundaries without any ambiguity:
   ```json
   {
     "stream_id": "synth_mix_001",
     "total_bytes": 16384,
     "segments": [
       {"start": 0, "end": 2048, "category": "CODE", "arch": "x86_64"},
       {"start": 2048, "end": 2064, "category": "PADDING", "arch": "NONE"},
       {"start": 2064, "end": 4112, "category": "DATA_STRING", "arch": "NONE"},
       {"start": 4112, "end": 6160, "category": "CODE", "arch": "arm32_thumb"},
       {"start": 6160, "end": 8208, "category": "DATA_TABLE", "arch": "NONE"},
       {"start": 8208, "end": 12304, "category": "COMPRESSED_OPAQUE", "arch": "NONE"},
       {"start": 12304, "end": 16384, "category": "CODE", "arch": "riscv"}
     ]
   }
   ```
4. **Partitioning & Leakage Prevention:**
   - Synthetic mixtures used for evaluation are built **strictly from test-split binaries**; no chunk from training or validation binaries may ever enter the test evaluation pool.

