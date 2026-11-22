# API Reference & Data Structures

**Project:** KETHRAVAX  
**Module:** `kethravax`  

---

## 1. Top-Level Classes

### `BinarySegmenter`

The primary inference and analysis orchestrator.

#### Methods

- `BinarySegmenter.from_pretrained(model_name: str = "default", device: str = "cpu") -> BinarySegmenter`  
  Loads a pre-trained KethraSeg model from local weights.

- `segmenter.analyze_file(file_path: str) -> SegmentationResult`  
  Performs full structural segmentation on a binary file on disk.

- `segmenter.analyze_bytes(data: bytes, stream_id: str = "stream") -> SegmentationResult`  
  Performs structural segmentation on an in-memory byte buffer.

---

### `SegmentationResult`

Represents the complete segmentation analysis for an input stream.

#### Attributes

- `stream_id: str`: Identifier or filename of the stream.
- `total_bytes: int`: Total byte length of the input stream.
- `segments: List[Segment]`: Contiguous sequence of non-overlapping segments.
- `metadata: Dict[str, Any]`: Execution metadata (engine, device, format).

#### Methods

- `validate_invariants() -> Tuple[bool, Optional[str]]`: Verifies total coverage, contiguity, and disjointness.
- `to_dict() -> Dict[str, Any]`: Serializes to dictionary.
- `to_json(indent: int = 2) -> str`: Exports formatted JSON.
- `from_dict(data: Dict[str, Any]) -> SegmentationResult`: Deserializes from dictionary.

---

### `Segment`

Represents an individual structural segment.

#### Attributes

- `start: int`: Inclusive start offset in the byte stream (`>= 0`).
- `end: int`: Exclusive end offset in the byte stream (`> start`).
- `length: int`: Computed property (`end - start`).
- `category: StructuralCategory`: Predicted structural category.
- `arch: Architecture`: Predicted CPU architecture (`NONE` for non-code categories).
- `confidence: float`: Calibrated model confidence in `[0.0, 1.0]`.
- `diagnostics: Dict[str, Any]`: Diagnostic dictionary containing local Shannon entropy, null ratio, printable ratio, and alternative predictions.

---

## 2. Enums

### `StructuralCategory`

- `CODE`: Executable machine instructions.
- `DATA_STRING`: Printable text pools and string literals.
- `DATA_TABLE`: Relocation entries, jump tables, pointer arrays.
- `DATA_RAW`: Initialized constant data structures and headers.
- `PADDING`: Alignment bytes (`0x00`, `0x90`, `0xCC`).
- `COMPRESSED_OPAQUE`: High-entropy zlib/gzip payloads or cryptographic blocks.
- `UNKNOWN_AMBIGUOUS`: Unresolved or conflicting byte sequences.

### `Architecture`

- `NONE`: Inactive (non-code regions).
- `X86_64`: x86 64-bit (AMD64 / Intel 64).
- `X86_32`: x86 32-bit (IA-32).
- `ARM32_ARM`: ARM 32-bit ARM instruction state.
- `ARM32_THUMB`: ARM 16/32-bit Thumb / Thumb-2 state.
- `AARCH64`: ARM 64-bit (ARMv8-A/ARMv9-A).
- `MIPS32`: MIPS32 Big / Little Endian.
- `RISCV`: RISC-V (RV32 / RV64).
- `ARCH_UNKNOWN`: Executable code confirmed, but architecture unresolved.

