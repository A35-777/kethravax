# Dataset Card: KETHRAVAX Multi-Class Binary Structural Corpus

**Dataset Name:** KethraCorpus-v1  
**Version:** 1.0.0  
**Curator:** Kethravax Core AI Research Team  
**License:** Permissive (Apache 2.0 / MIT compatible)  
**Task:** Dense Multi-Class Structural Byte-Stream Segmentation & ISA Discovery  

---

## 1. Dataset Summary

The **KethraCorpus-v1** dataset is designed for training and rigorously benchmarking machine-learning and deep neural architectures on the task of **headerless multi-class structural byte-stream segmentation**.

Unlike existing binary datasets (e.g. EMBER, SOREL-20M, Binary-30K) that provide whole-file metadata or coarse file-level labels, KethraCorpus provides **dense byte-level ground-truth segment annotations** `[start_offset, end_offset, category, arch]` across every contiguous byte range from offset 0 to EOF.

---

## 2. Dataset Composition & Partitioning

KethraCorpus-v1 is split into two cleanly separated tracks:

### Track A: Real-World Compiled Binaries
- **Sources:** Debian Linux packages, OpenWrt firmware builds, and Windows Python/MSVC executables and dynamic libraries (`python.exe`, `python3.13t.exe`, `t32.exe`, `t64.exe`, `.pyd`, ELF shared objects).
- **Architectures:**
  - `x86_64` (AMD64 / Intel 64)
  - `x86_32` (IA-32)
  - `arm32_thumb` / `arm32_arm`
  - `aarch64`
  - `mips32`
  - `riscv`
- **Annotation Method:** Verified structural extraction using section headers, symbol tables, mapping symbols (`$a`, `$t`, `$d`), and relocation entries.
- **Deduplication:** Hashed via SHA-256; zero byte-identical files exist across splits.

### Track B: Controlled Multi-Class Synthetic Mixtures
- **Purpose:** Rigorous stress-testing of **mixed-architecture streams**, **headerless slices**, and **fine-grained boundary localization**.
- **Composition:** Assembles contiguous segments of compiled instruction sequences, string literal pools, pointer/jump tables, alignment padding, and zlib compressed streams.
- **Isolation:** Evaluation mixtures are built strictly from held-out source binaries that are absent from the training set.

### Official Splits & Leakage Prevention

| Split | Stream Count | Total Bytes | Unique Projects | Synthetic vs Real | Leakage Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Train** | 60 | ~1,250,000 | 12 | 50% Real / 50% Synth | **CLEAN (0% Leakage)** |
| **Validation** | 20 | ~420,000 | 4 | 50% Real / 50% Synth | **CLEAN (0% Leakage)** |
| **Test (In-Distribution)** | 20 | ~420,000 | 4 | 50% Real / 50% Synth | **CLEAN (0% Leakage)** |
| **Test (Unseen Real / Mixed)** | 20 | ~500,000 | 6 (Held-out) | 100% Real & Mixed | **CLEAN (0% Leakage)** |

---

## 3. Label Taxonomy & Distribution

Ground-truth categories represented:
1. `CODE`: Executable instructions annotated with target ISA (`x86_64`, `x86_32`, `arm32_arm`, `arm32_thumb`, `aarch64`, `mips32`, `riscv`).
2. `DATA_STRING`: Printable text pools, error strings, format strings.
3. `DATA_TABLE`: Relocation entries, jump tables, pointer arrays.
4. `DATA_RAW`: Initialized non-string constant structures and headers.
5. `PADDING`: Null runs (`0x00`), NOP sleds (`0x90`), int3 fill (`0xCC`).
6. `COMPRESSED_OPAQUE`: High-entropy zlib/gzip payloads and cryptographic blocks.
7. `UNKNOWN_AMBIGUOUS`: Unresolved, conflicting, or truncated bytes.

---

## 4. Invariants & Data Integrity

Every ground-truth annotation in KethraCorpus guarantees:
- **Zero Loss / Total Coverage:** $\text{start}_0 = 0$ and $\text{end}_{M-1} = \text{total\_bytes}$.
- **Contiguity:** $\text{end}_k = \text{start}_{k+1}$.
- **No Zero-Length Segments:** $\text{end}_k > \text{start}_k$.
- **No Overlaps:** Segments are strictly disjoint.

