# Competitor & Systems Matrix: Binary Analysis & Stream Segmentation

**Document Version:** 1.0.0  
**Project:** KETHRAVAX  
**Classification:** Comparative Systems Engineering  
**Date:** 2026-11-22  

---

## 1. Comparative Analysis Matrix

The table below benchmarks KETHRAVAX against twelve prominent systems across academia and open-source tooling.

| System | Primary Function | Granularity | Requires Headers? | Supported Categories | Supports Mixed Structures? | Exact Byte Boundaries? | Uses ML / Neural? | Open Source License | Unaddressed Capability Gap |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: | :--- | :--- |
| **KETHRAVAX** (Ours) | Multi-class structural stream segmentation & ISA discovery | Byte-level contiguous segments `[start, end)` | **No** (Raw bytes) | Code, 7 ISAs, String pools, Jump/Data tables, Padding, Compressed/Opaque, Unknown | **Yes** | **Yes** (Exact byte snapping) | **Yes** (TCN / Hybrid / BiLSTM + Boundary Head) | Apache 2.0 / MIT | Complete unaddressed union: multi-class, multi-architecture, exact-offset, headerless. |
| **ELISA** (Polino et al.) | Code discovery & code/data separation | Instruction / Basic Block | No | Code vs Data (Binary) | No (Single ISA per file) | Coarse (Block level) | Yes (Linear-Chain CRF + Logistic Regression) | Research code | Binary classification only; slow CRF inference; no mixed-architecture support. |
| **Remigio et al.** (IWSEC 2023) | Firmware section boundary detection | Macro sections | No | Code section vs Data section | No | Coarse (±64B jitter) | Yes (BiLSTM + heuristics) | Academic paper | Section-level only; smearing at boundaries; lacks multi-class data taxonomy. |
| **cpu_rec** (Airbus-seclab) | Architecture identification | Large sliding window (4KB+) | No | 70+ CPU architectures (Code only) | Weak | No (Window level) | No (Statistical n-gram KL divergence) | Apache 2.0 | Cannot segment non-code data; blind to fine-grained boundaries (<512B). |
| **ISAdetect** (Costin et al.) | Architecture & endianness identification | Whole binary / chunk | No | 15+ CPU architectures & Endianness | No | No (File/Chunk level) | Yes (Random Forest, SVM, k-NN) | GPL-3.0 | Whole file/chunk classifier; no boundary detection; no data classification. |
| **Magika** (Google) | File content-type detection | Whole file | Partial (Samples 512B chunks) | 100+ standard file types (PDF, ELF, ZIP, etc.) | No | No (Single label per file) | Yes (Compact 1D CNN) | Apache 2.0 | File-level classification; cannot segment internal regions of a single file. |
| **FiFTy** (Mittal et al.) | File fragment type identification | Fixed blocks (512B / 4KB) | No | 75 file types (Sector level) | No | No (Block level) | Yes (1D CNN embedding) | MIT | Fixed-block classification; no sequential stream boundaries; no sub-file internal structure. |
| **Binary-30K** (Bommarito et al.) | Multi-platform binary dataset & benchmark | File level | Yes (LIEF parsing) | Executables across 15+ architectures | N/A | N/A (Dataset) | Yes (BPE Tokenizer + Transformer baselines) | Apache 2.0 | Dataset only; lacks dense byte-level ground truth masks. |
| **XDA** (NDSS 2022) | Function and instruction boundary recovery | Byte/token level | Assumes Code | Instructions, Function entry/exit | No (x86/x64 code only) | Yes (Inside code) | Yes (Transformer MLM) | Academic open-source | Heavyweight Transformer; strictly analyzes compiled x86 code; ignores arbitrary data. |
| **DeepDi** (USENIX 2022) | Superset instruction disassembly & flow graph recovery | Instruction level | Assumes Code | Instructions, Function boundaries | No (x86/x64 only) | Yes (Inside code) | Yes (Relational GNN) | GPL-3.0 | Disassembler only; requires known architecture; cannot segment raw mixed streams. |
| **Binwalk** (ReFirmLabs) | Firmware extraction & signature carving | Magic signature offsets | No | Archive & compression headers (gzip, squashfs, etc.) | Partial (Carves sub-files) | Header start only (no end offsets) | No (Regex/Magic signatures) | MIT | High false positive rate; blind to raw code, jump tables, and unmagic structured data. |
| **Unblob** (ONEKEY) | Accurate firmware unpacking & carving | Format chunk | No | 78+ archive & container formats | Partial (Carves sub-files) | Format bounds | No (Heuristic & parser rules) | Apache 2.0 | Carves structured containers; does not analyze raw machine instructions or bare data tables. |
| **PolyFile** (Trail of Bits) | Polyglot file format identification | Syntactic byte spans | Yes/Partial | Grammars specified in Kaitai Struct | Yes (Polyglots) | Yes (Grammar spans) | No (Pure Python libmagic + Kaitai) | Apache 2.0 | Dependent on known file format grammars; fails on unstructured raw byte streams. |

---

## 2. In-Depth System Profiles & Practical Tradeoffs

### 2.1 Direct Competitors
- **ELISA & Remigio et al. (BiLSTM):**
  - *Direct relevance:* These are the closest direct academic predecessors addressing code/data separation in headerless binaries.
  - *Why KETHRAVAX advances state-of-the-art:* Both systems restrict their scope to a 2-class problem (`CODE` vs `DATA`) and suffer from boundary localization degradation. KETHRAVAX expands the task to a multi-class taxonomy (Code, Architectures, Strings, Tables, Padding, Opaque) and employs exact byte-snapping.

### 2.2 Complementary & Adjacent Systems
- **cpu_rec & ISAdetect:**
  - *Role:* Excellent as complementary baselines and validation oracles for architecture verification over identified `CODE` regions.
- **Binwalk & Unblob:**
  - *Role:* Downstream consumers of KETHRAVAX's structural segments. For example, KETHRAVAX can detect an unheadered compressed stream or code region, allowing Unblob to target carving without brute-force false positives.
- **PolyFile:**
  - *Role:* PolyFile excels when formal format specifications exist. KETHRAVAX steps in precisely where formal format specifications fail (raw firmware dumps, memory dumps, stripped monolithic microcode).

