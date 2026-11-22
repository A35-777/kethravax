# Next Steps & Production Horizons: KETHRAVAX

**Document Version:** 1.0.0  
**Status:** Post-v0.1.0 Plan  

---

## 1. Immediate Next Steps (v0.2.0)

1. **ONNX Runtime Export:**
   - Export `KethraSeg-Hybrid` to ONNX format with dynamic axis support for variable-length streams.
   - Benchmark inference speedup with ONNX Runtime CPU execution provider (targeting sub-10ms for 64 KB blocks).

2. **Quantization to INT8:**
   - Post-training quantization of convolutional and recurrent weights to INT8 to enable real-time execution on low-power edge microcontrollers (e.g. Raspberry Pi, ARM Cortex-A).

3. **Expanded Architecture Corpus:**
   - Incorporate real-world firmware dumps for SuperH (SH-4), SPARC, and PowerPC.

---

## 2. Reverse Engineering Tool Integrations (v0.3.0)

1. **Ghidra Extension:**
   - Develop a Java/Python Ghidra plugin that invokes `kethravax analyze --format json` and automatically applies memory block tags and disassembler hints.

2. **Radare2 / Rizin Integration:**
   - Custom Rizin r2pipe script creating flags and metadata comments across detected structural boundaries.

3. **Binary Ninja Plugin:**
   - Architecture discovery hook that guides linear sweep disassembly using Kethravax segment bounds.

