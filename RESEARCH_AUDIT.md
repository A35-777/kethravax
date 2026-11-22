# Research Audit: Binary Code/Data Separation, Architecture Identification & Stream Segmentation

**Document Version:** 1.0.0  
**Project:** KETHRAVAX  
**Classification:** Technical Research Foundation  
**Date:** 2026-11-22  

---

## 1. Executive Summary & Problem Landscape

A foundational problem in software reverse engineering, IoT firmware security, memory forensics, and binary vulnerability analysis is the **structural interpretation of headerless byte streams**.

Traditional reverse engineering frameworks (IDA Pro, Ghidra, Radare2, Binary Ninja) rely heavily on container file headers (ELF, Portable Executable, Mach-O) to locate entry points, segment boundaries, and instruction sets. When faced with raw firmware dumps, corrupted images, memory dumps, or stage-2 shellcode, existing tools suffer from severe failure modes:
1. They misinterpret embedded data (jump tables, literal pools, string constants) as executable instructions, triggering catastrophic disassembler desynchronization (especially in variable-length ISAs like x86/x64).
2. They cannot determine which segments are written in which Instruction Set Architecture (ISA) when multi-architecture codebases coexist (e.g., ARM32/Thumb interworking, bootloaders switching from 16-bit real mode to 32/64-bit protected mode, or firmware containing secondary co-processor microcode like MIPS or RISC-V).
3. They lack multi-class structural awareness: they classify binaries as either coarse "code vs data", or they treat whole files as single formats, unable to segment contiguous sub-ranges into structured string pools, lookup tables, alignment padding, or high-entropy encrypted blobs.

This audit examines the state-of-the-art literature, analyzes existing tools, and establishes the precise research and technical gap addressed by **KETHRAVAX**.

---

## 2. In-Depth Prior Research Analysis

### 2.1 ELISA: Eliciting ISA of Raw Binaries for Fine-Grained Code and Data Separation
- **Authors & Publication:** Mario Polino et al. (Politecnico di Milano).
- **Core Mechanism:** ELISA proposes a two-stage pipeline for analyzing raw firmware binaries:
  1. *ISA Elicitation:* Logistic regression trained on byte n-gram frequencies to predict the underlying architecture.
  2. *Code/Data Separation:* Sequential labeling using a Linear-Chain Conditional Random Field (Linear-Chain CRF). Features include opcode validity, instruction length consistency, and statistical byte entropy.
- **Strengths:** 
  - Pioneered fine-grained byte-level classification of code vs data in raw binaries.
  - Successfully demonstrated that sequential probabilistic models (CRFs) prevent isolated single-byte misclassifications by enforcing sequence transition consistency.
- **Critical Limitations:**
  - *Binary Only:* Strictly predicts two classes: `CODE` vs `DATA`. It cannot distinguish string tables, jump tables, alignment padding, or compressed sub-chunks.
  - *Computational Bottleneck:* CRF inference scales quadratically with label count and linearly with sequence length, making it intractable for large binaries without aggressive chunking.
  - *Single Architecture Assumption:* Assumes the entire binary belongs to one statically elicited architecture; cannot handle mixed-architecture streams (e.g., ARM/Thumb transitions, or mixed micro-controller payloads).
  - *Fragility on Packed/High-Entropy Code:* Fails when instructions exhibit high entropy or non-standard encodings.

### 2.2 "The Good, the Bad, and the Binary: An LSTM-Based Method for Section Boundary Detection in Firmware Analysis"
- **Authors & Publication:** Riccardo Remigio, Alessandro Bertani, Mario Polino, Michele Carminati, Stefano Zanero (IWSEC 2023, Lecture Notes in Computer Science).
- **Core Mechanism:**
  - Evaluates section boundary detection on IoT firmware images lacking ELF/PE headers.
  - Replaces ELISA's Linear-Chain CRF with a Bidirectional Long Short-Term Memory (BiLSTM) network paired with post-processing heuristics.
  - Introduces an entropy-based architecture classification step specifically designed to detect whether binaries are packed or compressed prior to ISA classification.
- **Strengths:**
  - BiLSTM captures bidirectional context (both preceding function prologues and following epilogues/returns).
  - Substantially improves section-level boundary recovery over ELISA on firmware datasets.
  - Demonstrates that deep recurrent representations outperform hand-crafted CRF features on complex IoT firmware.
- **Critical Limitations:**
  - *Coarse Granularity:* Primary objective is macroscopic section boundary detection (e.g., finding the boundary between `.text` and `.rodata`), not dense multi-class structural segmentation.
  - *Binary Taxonomy:* Still framed essentially as code vs non-code section separation.
  - *Boundary Smearing:* Recurrent hidden states cause boundary localization jitter (often ±64 to ±256 bytes from the true section offset), requiring ad-hoc threshold heuristics.
  - *Uncertainty Modeling:* Lacks calibrated confidence output; outputs raw softmax probabilities that are overconfident near boundary transitions.

### 2.3 cpu_rec (Airbus-seclab)
- **Mechanism:** Corpus-based statistical analysis using byte n-gram frequency distributions and Kullback-Leibler (KL) divergence against an extensive database of known architectures.
- **Strengths:** Lightweight, supports over 70 CPU architectures, robust against large chunks of uncorrupted code.
- **Limitations:** Sliding window approach (typically 4 KB to 64 KB). Cannot detect fine-grained boundaries (<512 bytes), completely fails on non-executable structures, and cannot segment multi-class data.

### 2.4 Magika (Google, 2024)
- **Mechanism:** Deep learning file-type identification using a lightweight 1D CNN with sparse byte sampling (e.g., inspecting the first 512 bytes, middle 512 bytes, and tail 512 bytes).
- **Strengths:** High CPU inference speed (<5 ms), ~99% precision/recall across 100+ standard file formats.
- **Limitations:** Magika is a **whole-file classifier**, not a **stream segmenter**. It assigns a single file-type label to an entire file. It cannot provide a sequence of contiguous byte-offset segments `[start, end, label]` for heterogeneous binary streams.

### 2.5 FiFTy (Mittal et al.)
- **Mechanism:** Compact Convolutional Neural Network trained on raw byte embeddings for block-level file fragment classification (512-byte and 4096-byte sectors on the FFT-75 dataset).
- **Strengths:** Avoids hand-crafted features, scales to 75 file types.
- **Limitations:** Isolated block classification. It treats each 512B/4KB block independently without continuous sequential transition context, cannot localize exact byte boundaries, and does not classify sub-executable internal structures (e.g., jump tables vs code vs strings).

### 2.6 XDA (NDSS 2022) & DeepDi (USENIX Security 2022)
- **Mechanisms:**
  - *XDA:* Self-supervised Masked Byte Language Model (Transformer) for function boundary and assembly recovery.
  - *DeepDi:* Superset disassembly followed by Relational Graph Convolutional Networks (RGCN) on Instruction Flow Graphs.
- **Strengths:** State-of-the-art precision for instruction boundary recovery in compiled x86/x64 binaries.
- **Limitations:** Both require pre-known architecture and executable context. They are heavy disassemblers rather than multi-class structural segmenters for raw, unknown byte streams.

### 2.7 Unblob, Binwalk, & PolyFile
- **Binwalk / Unblob:** Fast signature carvers searching for known archive/filesystem magic bytes (e.g. gzip, squashfs, lzma). Blind to raw code, jump tables, or unmagic data.
- **PolyFile:** Cleanroom Python parser utilizing Kaitai Struct grammars. Excellent for formal file formats and nested polyglots, but incapable of parsing raw, unheadered, arbitrary binary streams lacking a known grammar.

---

## 3. The Unaddressed Capability: What KETHRAVAX Solves

Across the academic literature and industrial tooling, a distinct capability gap remains unaddressed:

| Capability | ELISA | Remigio et al. | cpu_rec | Magika | FiFTy | Binwalk | **KETHRAVAX** |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Headerless Raw Stream Processing** | Yes | Yes | Yes | Partial | Yes | Yes | **Yes** |
| **Multi-Class Structural Taxonomy** (Code, Strings, Tables, Padding, Opaque) | No (2 classes) | No (2 classes) | No | No (File-type) | No (File-type) | No (Carve-only) | **Yes (7+ Classes)** |
| **Multi-Architecture Code Identification** | Single | Single | Sliding window | No | No | No | **Yes (Hierarchical)** |
| **Exact Byte Offset Boundary Recovery** | Rough | Coarse (±64B) | None | None | Block-only | Magic-only | **Exact Byte-Snapping** |
| **Mixed-Architecture Stream Support** | No | No | Partial | No | No | No | **Yes** |
| **Uncertainty / Ambiguity Quantification** | No | No | Heuristic | Softmax | Softmax | None | **Calibrated Confidence** |
| **Dense Byte-Level Ground Truth Evaluation** | Basic block | Section | None | File | Block | Magic | **Dense Byte IoU/F1** |

---

## 4. Key Scientific Hypotheses for KETHRAVAX

1. **Hypothesis 1 (Structural Learnability):**
   Byte streams possess distinct multi-scale statistical and syntactic signatures:
   - *Code:* High local opcode density, repetitive register prefix bytes (e.g. `0x48`, `0x49` in x86-64), structured branch target offsets, low null density.
   - *Strings:* High concentration of printable ASCII (`0x20`-`0x7E`) or UTF-8 multi-byte sequences terminated by `0x00`.
   - *Tables / Pointer Arrays:* Low entropy, periodic 4-byte or 8-byte aligned values within the virtual address range of the binary, monotonic or clustered jump offsets.
   - *Padding:* Homogeneous sequences of `0x00` (null padding), `0x90` (NOP sleds), `0xCC` (int3), or `0x00000000` / `0x0000a0e1` (ARM `nop`).
   - *Compressed / Opaque:* Shannon entropy approaching 8.0 bits/byte with uniform chi-square distribution.
   - *These signatures can be jointly modeled by a multiscale convolutional-recurrent architecture without file headers.*

2. **Hypothesis 2 (Boundary Precision via Dual-Head Learning):**
   Coarse window classification models smear transition boundaries. By pairing a sequence-labeling head with an explicit boundary-transition detection head (or local gradient snapping), boundary localization error can be reduced from ±64 bytes down to exact byte offsets.

3. **Hypothesis 3 (Hierarchical Architecture Disentanglement):**
   Decoupling the structural family (`CODE`, `DATA`, `PADDING`, etc.) from the architecture label prevents non-code bytes from polluting architecture classifiers, yielding higher architecture macro-F1 on mixed streams.

