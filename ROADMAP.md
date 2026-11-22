# Project Roadmap: KETHRAVAX

**Document Version:** 1.0.0  
**Status:** Active Execution  
**Target Milestone:** v0.1.0 Beta Release  

---

## Phase Milestones & Strategic Timeline

### Milestone 1: v0.1.0-alpha (Foundation & Validation) — Current
- [x] Comprehensive research audit comparing ELISA, Remigio et al. (BiLSTM), cpu_rec, ISAdetect, Magika, FiFTy, Binary-30K.
- [x] Brand clearance and taxonomy formalization across 7 structural categories and 7 instruction architectures.
- [x] Pure-Python ground-truth extraction for PE and ELF binaries, with mapping symbol resolution ($a, $t, $d).
- [x] Deterministic synthetic mixture generator for mixed-architecture and headerless stream evaluation.
- [x] Initial baselines: Entropy Heuristic, Random Forest, BiLSTM, Dilated TCN, KethraSeg-Hybrid.
- [x] Pure client-side Interactive Binary Explorer with hex view, timeline ruler, and JSON export.

### Milestone 2: v0.2.0 (Model Optimization & Fine-Grained Snapping)
- [ ] Export trained KethraSeg models to ONNX runtime for sub-10ms CPU inference.
- [ ] Quantization to INT8 for resource-constrained embedded edge devices.
- [ ] Support for Mach-O 64-bit ground-truth section parsing.
- [ ] Expanded architecture coverage: SuperH (SH-4), SPARC, PowerPC.

### Milestone 3: v0.3.0 (Ecosystem & Reverse Engineering Tool Integrations)
- [ ] Ghidra Headless Extension: Automated structural segment script importing Kethravax segment manifests to guide memory mapping and disassembler pass.
- [ ] Radare2 / Rizin plugin: Command `!kethravax <file>` overlaying structural flags into Rizin database.
- [ ] Binary Ninja integration via Python API.

### Milestone 4: v1.0.0 (Production Release & Open Science Dataset)
- [ ] Publication of expanded real-world benchmark on 5,000+ firmware dumps.
- [ ] Pre-trained model weights hosted on Hugging Face Hub under `kethravax/kethraseg-hybrid`.
- [ ] Multi-threaded batch ingestion CLI processing directories of binaries concurrently.

