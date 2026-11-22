# Quickstart Tutorial

Learn how to use **KETHRAVAX** in 5 minutes via the Python SDK and Command-Line Interface (CLI).

---

## 1. Python SDK Usage

### Basic File Analysis

```python
from kethravax import BinarySegmenter

# Load the production KethraSeg model
segmenter = BinarySegmenter.from_pretrained("default")

# Analyze an arbitrary binary file
result = segmenter.analyze_file("firmware_dump.bin")

print(f"Stream: {result.stream_id} | Total Size: {result.total_bytes:,} bytes")
print(f"Detected {len(result.segments)} contiguous structural segments:\n")

for seg in result.segments:
    arch_str = f" ({seg.arch.value})" if seg.category.value == "CODE" else ""
    print(
        f"[{seg.start:#010x} - {seg.end:#010x}) "
        f"{seg.category.value:<18} {arch_str:<12} "
        f"Length: {seg.length:<8} Conf: {seg.confidence * 100:5.1f}%"
    )
```

### In-Memory Byte Stream Analysis

```python
import os
from kethravax import BinarySegmenter

segmenter = BinarySegmenter.from_pretrained("default")

# Analyze in-memory byte buffers directly
raw_bytes = os.urandom(1024)
result = segmenter.analyze_bytes(raw_bytes, stream_id="memory_buffer")

# Export to structured JSON
json_manifest = result.to_json(indent=2)
print(json_manifest)
```

---

## 2. Command-Line Interface (CLI)

### Analyze a File (Terminal Table)

```bash
kethravax analyze firmware.bin
```

Example terminal output:
```text
================================================================================================
KETHRAVAX STRUCTURAL SEGMENTATION REPORT: firmware.bin
Total Stream Length: 65,536 bytes | Detected Segments: 7
================================================================================================
Start        End          Length     Category               Arch           Conf     Entropy
------------------------------------------------------------------------------------------------
0x00000000   0x00000200   512        DATA_RAW               -              98.2%    4.12 b/B
0x00000200   0x00004800   17408      CODE                   arm32_thumb    94.5%    5.88 b/B
0x00004800   0x00004840   64         PADDING                -              99.8%    0.00 b/B
0x00004840   0x00006200   6592       DATA_STRING            -              96.1%    4.35 b/B
0x00006200   0x00007800   5632       DATA_TABLE             -              91.0%    2.40 b/B
0x00007800   0x0000F000   30720      COMPRESSED_OPAQUE      -              99.1%    7.92 b/B
0x0000F000   0x00010000   4096       CODE                   riscv          92.3%    5.91 b/B
------------------------------------------------------------------------------------------------
```

### Export Directly to JSON

```bash
kethravax analyze firmware.bin --format json -o segmentation.json
```

### Inspect Specific Byte Offsets and Hex Dump

```bash
kethravax inspect firmware.bin --offset 0x00004840 --length 128
```

### View Benchmark Results Against Baselines

```bash
kethravax benchmark
```

