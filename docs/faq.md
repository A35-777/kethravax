# Frequently Asked Questions (FAQ)

### What makes KETHRAVAX different from Magika?
**Magika** is a *whole-file classifier* developed by Google. Given a file, it outputs a single label predicting what kind of file it is (e.g., "This file is a PDF" or "This file is an ELF executable").  
**KETHRAVAX** is a *multi-class structural stream segmenter*. It operates on raw, headerless byte streams and outputs a sequence of contiguous byte-offset intervals `[start, end)` identifying where code, string literal pools, jump tables, alignment padding, and compressed payloads begin and end within the stream.

### What makes KETHRAVAX different from Binwalk or Unblob?
**Binwalk** and **Unblob** are *carvers* that search for known container headers and compression magic bytes (e.g., gzip magic `0x1F 0x8B`, squashfs magic `hsqs`).  
When an executable region, jump table, or raw string pool has no container header, signature carvers are completely blind to it. KETHRAVAX uses learned neural sequence representations to identify structural regions without needing magic numbers.

### What makes KETHRAVAX different from ELISA and Remigio et al.?
Earlier research (ELISA, Remigio et al. IWSEC 2023) formulated the problem strictly as a 2-class binary distinction (`CODE` vs `DATA`), and evaluated section-level cuts on firmware dumps.  
KETHRAVAX expands the task to a comprehensive 7-class structural taxonomy (separating string pools, pointer tables, padding, and opaque payloads), identifies specific CPU architectures for code segments, and employs exact byte-snapping to eliminate boundary localization jitter.

### Can KETHRAVAX handle mixed-architecture streams?
Yes. KETHRAVAX explicitly supports streams containing multiple instruction set architectures (such as ARM32/Thumb interworking, or firmware images containing host code and co-processor microcode).

### Does KETHRAVAX execute the analyzed files?
**No, never.** KETHRAVAX is strictly static and observational. Input bytes are ingested as numeric tensor values and never executed.

