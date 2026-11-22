# Known Limitations & Honest Failure Modes

**Project:** KETHRAVAX  
**Classification:** Engineering Transparency  
**Date:** 2026-11-22  

---

## 1. Executive Summary

In adherence to scientific integrity principles, this document enumerates the verified failure modes, theoretical boundaries, and operational constraints of KETHRAVAX.

No AI model can solve every reverse-engineering challenge from raw bytes alone without ground-truth symbol information. KETHRAVAX expresses calibrated uncertainty rather than fabricating false certainty.

---

## 2. Fundamental Technical Limitations

### 2.1 Ambiguity in Extremely Short Sequences (<16 Bytes)
- **The Problem:** In CISC architectures (e.g. x86-64), a sequence of 4 to 8 bytes can simultaneously decode as valid machine instructions, represent a 32-bit float or integer constant in `.rodata`, or form a short ASCII identifier (e.g. `USER`, `HTTP`).
- **Mitigation:** The model marks segments shorter than 16 bytes that lack distinctive surrounding context with lower confidence ($c < 0.50$) or labels them `UNKNOWN_AMBIGUOUS`.

### 2.2 Distinguishing Encrypted from Compressed Payloads
- **The Problem:** Both modern cryptographic streams (AES-GCM, ChaCha20) and modern high-compression streams (Zstandard, LZMA, Deflate) produce Shannon entropy approaching theoretical maximum ($H \approx 7.95$ bits/byte) and uniform byte distributions.
- **Limitation:** Pure byte-level statistics cannot reliably separate encrypted blobs from raw compressed payloads without format-specific magic headers.
- **Taxonomy Decision:** Both categories are unified under `COMPRESSED_OPAQUE` to prevent misleading predictions.

### 2.3 Stripped Monolithic Thumb-2 vs ARM State
- **The Problem:** ARMv7 processors can dynamically switch between 32-bit ARM mode and mixed 16/32-bit Thumb state via `BX`/`BLX` instructions. In stripped monolithic firmware dumps lacking `$a` and `$t` mapping symbols, short Thumb-2 functions with 32-bit wide instructions can mimic ARM-state opcodes.
- **Mitigation:** KETHRAVAX uses bidirectional sequence modeling to track average opcode alignment and branch targets, but edge-case transitions may exhibit ±4 byte localization jitter.

### 2.4 Uninitialized BSS Memory
- **The Problem:** `.bss` sections occupy virtual memory space at runtime, but occupy zero bytes in binary files on disk.
- **Rule:** KETHRAVAX analyzes byte streams. Memory allocated at runtime that has no byte manifestation in the stream cannot be detected.

---

## 3. Operational Bounds & Resource Constraints

| Metric | Tested Operational Bound | Behavior Beyond Bound |
| :--- | :--- | :--- |
| **Max Single-File Size** | 100 MB | Files >100 MB should be analyzed via streaming chunks or sub-slices to stay within 8 GB RAM bounds. |
| **Minimum Segment Size** | 16 bytes | Sub-16-byte fragments are coalesced into enclosing or adjacent segments. |
| **Inference Hardware** | CPU (AVX2 recommended) | Runs reliably on 4-core CPUs; throughput scales linearly with core count. |
| **Unsupported Formats** | Proprietary encrypted containers (DRM, BitLocker) | Classified globally as `COMPRESSED_OPAQUE`. |

