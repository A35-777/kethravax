# Changelog

All notable changes to **KETHRAVAX** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-11-22

### Added
- **Core Types & Taxonomy:** Formalized 7 structural categories (`CODE`, `DATA_STRING`, `DATA_TABLE`, `DATA_RAW`, `PADDING`, `COMPRESSED_OPAQUE`, `UNKNOWN_AMBIGUOUS`) and 7 instruction architectures (`x86_64`, `x86_32`, `arm32_arm`, `arm32_thumb`, `aarch64`, `mips32`, `riscv`).
- **Ground-Truth Parsers:**
  - PE metadata parser extracting code, string pools, jump tables, and alignment padding.
  - Pure-Python ELF32/ELF64 parser supporting mapping symbol resolution (`$a`, `$t`, `$d`).
  - Synthetic stream mixture generator for mixed-architecture stress tests.
- **Models & Baselines:**
  - `EntropyHeuristicBaseline`: Shannon entropy and character-class rule baseline.
  - `ClassicalMLBaseline`: Random Forest classifier on sliding byte-frequency features.
  - `KethraSegBiLSTM`: Bidirectional LSTM baseline inspired by Remigio et al. (IWSEC 2023).
  - `KethraSegTCN`: Dilated Temporal Convolutional Network with residual blocks.
  - `KethraSegHybrid`: Flagship multiscale 1D CNN + BiGRU + Dual-Head boundary snapper.
- **Decoding Engine:** Boundary snapping via local gradient and null-discontinuity detection, guaranteeing exact byte coverage and non-overlapping contiguity.
- **Interactive Binary Explorer:** Client-side HTML/JS explorer with hex viewer, timeline minimap, and JSON export.
- **Python SDK & CLI:** `BinarySegmenter` API and `kethravax` CLI with `analyze`, `inspect`, `model-info`, and `benchmark` commands.
- **Evaluation Suite:** Dense byte IoU, macro/micro F1, boundary localization at $\tau \in \{0, 4, 16, 32\}$ bytes, and calibration metrics.

