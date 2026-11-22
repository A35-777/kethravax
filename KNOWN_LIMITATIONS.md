# Known Limitations & Empirical Constraints: KETHRAVAX

**Document Version:** 1.0.0  
**Status:** Maintained  
**Classification:** Scientific Integrity  

---

## 1. Ground-Truth Ambiguity & Micro-Sequences

- **Short-Span Ambiguity (<16 Bytes):**
  Short byte sequences in CISC architectures (e.g. x86-64) can be decoded as valid machine instructions or as numeric constants (e.g. 32-bit floats in `.rodata`).
  *Mitigation:* The model assigns lower confidence or marks the span as `UNKNOWN_AMBIGUOUS` when local context is insufficient.

- **Encrypted vs. Compressed Data Indistinguishability:**
  Both high-ratio compression algorithms (zlib, LZMA, Zstandard) and cryptographically secure pseudorandom streams (AES, ChaCha20) exhibit Shannon entropy $H \in [7.9, 8.0]$ bits/byte.
  *Design Decision:* Both payload types are grouped under `COMPRESSED_OPAQUE` to avoid ungrounded guesswork.

- **ARM32 vs. Thumb-2 State Transitions:**
  In raw firmware images lacking ELF mapping symbols (`$a`, `$t`), interworking transitions between 32-bit ARM mode and 16/32-bit Thumb-2 state may display up to ±4 bytes of boundary localization jitter.

---

## 2. Resource & Runtime Profile

- **Memory Bound:** Large files (>100 MB) should be processed via streaming window batches to ensure memory usage remains within 8 GB RAM limits.
- **CPU Target:** Designed and benchmarked CPU-first (AVX2/SSE4). No CUDA GPU is required.

