# Release Verification Checklist: KETHRAVAX v0.1.0

**Status Tracking:** Release Verification  
**Target Release:** v0.1.0 Beta  

---

## Verification Criteria

### 1. Research & Task Formalization
- [x] Brand clearance completed and documented (`BRAND_RESEARCH.md`).
- [x] Comprehensive research audit comparing ELISA, Remigio et al., cpu_rec, ISAdetect, Magika, FiFTy, Binary-30K (`RESEARCH_AUDIT.md`, `COMPETITOR_MATRIX.md`, `RELATED_WORK.md`).
- [x] Task definition and invariant specifications formalized (`TASK_DEFINITION.md`).
- [x] Ground-truth taxonomy and annotation guidelines documented (`LABEL_TAXONOMY.md`, `ANNOTATION_GUIDELINES.md`).

### 2. Dataset Engineering
- [x] PE parser with section, symbol, and alignment extraction.
- [x] Pure-Python ELF32/ELF64 parser with mapping symbol support ($a, $t, $d).
- [x] Deterministic synthetic mixture generator for mixed architectures.
- [x] Split deduplication and non-leakage verification.
- [x] Dataset card completed (`DATASET_CARD.md`).

### 3. Model & Benchmarks
- [x] Baselines implemented: Entropy Heuristic, Random Forest on byte features.
- [x] Neural models implemented: BiLSTM, Dilated TCN, KethraSeg-Hybrid.
- [x] Training pipeline executed from scratch on CPU.
- [x] Benchmark metrics compiled: Byte Accuracy, Macro F1, Macro IoU, Boundary localization F1 at $\tau \in \{0, 4, 16, 32\}$B, CPU throughput.
- [x] Model card documented (`MODEL_CARD.md`).

### 4. Software Product & Interfaces
- [x] Python SDK: `BinarySegmenter` with `from_pretrained`, `analyze_file`, `analyze_bytes`.
- [x] CLI executable: `kethravax analyze`, `inspect`, `model-info`, `benchmark`.
- [x] Structured JSON schema export preserving exact offsets.
- [x] Interactive Binary Explorer: self-contained HTML/JS web interface with hex viewer and timeline minimap (`explorer/index.html`).

### 5. Quality Assurance & Testing
- [x] Unit tests for core types, invariants, and metrics (`tests/unit/`).
- [x] Regression tests for edge cases: empty files, 1-byte, all zeros, random noise (`tests/regression/`).
- [x] Pytest suite passes cleanly.

### 6. Documentation & Packaging
- [x] `pyproject.toml` configuration with proper dependencies and scripts.
- [x] Documentation suite: `installation.md`, `quickstart.md`, `architecture.md`, `limitations.md`, `api.md`, `faq.md`.
- [x] Production website designed in `website/`.

