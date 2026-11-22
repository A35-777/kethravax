"""Kethravax Command-Line Interface (CLI)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List

from kethravax import __version__
from kethravax.core.taxonomy import ANSI_RESET, ARCH_COLORS, CATEGORY_COLORS, STRUCTURAL_CATEGORIES
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.inference.engine import BinarySegmenter
from kethravax.utils.entropy import calculate_byte_diagnostics


def format_hex_offset(offset: int) -> str:
    """Format integer byte offset as standard 8-digit hex."""
    return f"0x{offset:08X}"


def render_human_readable_segments(result: SegmentationResult) -> str:
    """Render a terminal table of structural segments."""
    lines = []
    lines.append("=" * 96)
    lines.append(f"KETHRAVAX STRUCTURAL SEGMENTATION REPORT: {result.stream_id}")
    lines.append(f"Total Stream Length: {result.total_bytes:,} bytes | Detected Segments: {len(result.segments)}")
    lines.append("=" * 96)
    lines.append(
        f"{'Start':<12} {'End':<12} {'Length':<10} {'Category':<22} {'Arch':<14} {'Conf':<8} {'Entropy'}"
    )
    lines.append("-" * 96)

    for seg in result.segments:
        cat_info = CATEGORY_COLORS.get(seg.category, {"ansi": "", "label": seg.category.value})
        ansi = cat_info.get("ansi", "")
        cat_str = f"{ansi}{seg.category.value:<20}{ANSI_RESET}"
        arch_str = seg.arch.value if seg.arch != Architecture.NONE else "-"
        conf_str = f"{seg.confidence * 100:5.1f}%"
        h = seg.diagnostics.get("entropy", "-")
        h_str = f"{h:.2f} b/B" if isinstance(h, (int, float)) else str(h)

        lines.append(
            f"{format_hex_offset(seg.start):<12} {format_hex_offset(seg.end):<12} {seg.length:<10} {cat_str:<30} {arch_str:<14} {conf_str:<8} {h_str}"
        )

    lines.append("-" * 96)
    return "\n".join(lines)


def render_hex_view(data: bytes, start: int = 0, length: int = 256) -> str:
    """Render a formatted hex dump with ASCII sidebar."""
    end = min(len(data), start + length)
    lines = []
    lines.append(f"\nHEX INSPECTION: [{format_hex_offset(start)} - {format_hex_offset(end)}) ({end - start} bytes)")
    lines.append("Offset    | 00 01 02 03 04 05 06 07  08 09 0A 0B 0C 0D 0E 0F | ASCII")
    lines.append("----------+-------------------------------------------------+-----------------")

    for row_start in range(start, end, 16):
        row_end = min(end, row_start + 16)
        row_bytes = data[row_start:row_end]
        hex_parts = []
        ascii_parts = []

        for b in row_bytes:
            hex_parts.append(f"{b:02X}")
            ascii_parts.append(chr(b) if 0x20 <= b <= 0x7E else ".")

        # Pad row to 16 bytes for alignment
        while len(hex_parts) < 16:
            hex_parts.append("  ")
            ascii_parts.append(" ")

        left_hex = " ".join(hex_parts[:8])
        right_hex = " ".join(hex_parts[8:])
        ascii_str = "".join(ascii_parts)

        lines.append(f"{row_start:08X}  | {left_hex}  {right_hex} | {ascii_str}")

    return "\n".join(lines)


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze a binary file."""
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    segmenter = BinarySegmenter.from_pretrained()
    result = segmenter.analyze_file(args.file)

    if args.format == "json":
        json_output = result.to_json(indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(json_output)
            print(f"Saved analysis to {args.output}")
        else:
            print(json_output)
    else:
        text_output = render_human_readable_segments(result)
        if args.output:
            with open(args.output, "w") as f:
                f.write(text_output)
            print(f"Saved report to {args.output}")
        else:
            print(text_output)

    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    """Inspect byte offsets and hexadecimal views."""
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}", file=sys.stderr)
        return 1

    with open(args.file, "rb") as f:
        data = f.read()

    offset = int(args.offset, 0) if isinstance(args.offset, str) else int(args.offset)
    length = int(args.length)

    segmenter = BinarySegmenter.from_pretrained()
    result = segmenter.analyze_bytes(data, stream_id=os.path.basename(args.file))

    # Find which segment contains this offset
    containing_seg = None
    for s in result.segments:
        if s.start <= offset < s.end:
            containing_seg = s
            break

    print("=" * 80)
    print(f"KETHRAVAX INSPECT: {args.file}")
    print(f"Target Offset: {format_hex_offset(offset)} ({offset:,} bytes)")
    if containing_seg:
        print(f"Enclosing Segment: [{format_hex_offset(containing_seg.start)} - {format_hex_offset(containing_seg.end)})")
        print(f"Category:          {containing_seg.category.value}")
        print(f"Architecture:      {containing_seg.arch.value}")
        print(f"Confidence:        {containing_seg.confidence * 100:.1f}%")
        print(f"Segment Diagnostics: {json.dumps(containing_seg.diagnostics)}")
    else:
        print("Offset falls outside file bounds.")

    hex_dump = render_hex_view(data, start=offset, length=length)
    print(hex_dump)
    return 0


def cmd_model_info(args: argparse.Namespace) -> int:
    """Display model metadata and architecture specifications."""
    print("=" * 80)
    print("KETHRAVAX NEURAL ARCHITECTURE & MODEL CARD")
    print("=" * 80)
    print("Model Family:           KethraSeg")
    print("Default Production:     KethraSeg-Hybrid (Multiscale CNN + BiGRU + Dual-Head)")
    print("Vocab:                  256 raw bytes (No OOV tokens)")
    print("Embedding Dimension:    48")
    print("Multiscale Kernels:     3, 5, 9, 17 (16 channels each = 64 conv channels)")
    print("Recurrent Backbone:     Bidirectional GRU (hidden_dim=36, bidirectional=True)")
    print("Structural Categories:  CODE, DATA_STRING, DATA_TABLE, DATA_RAW, PADDING, COMPRESSED_OPAQUE, UNKNOWN_AMBIGUOUS")
    print("Architectures:          x86_64, x86_32, arm32_arm, arm32_thumb, aarch64, mips32, riscv")
    print("Boundary Refinement:    Dual-head byte snapping with local gradient & null discontinuity detection")
    print("Execution Target:       CPU-first, zero GPU requirement, sub-100ms inference for 64KB blocks")
    return 0


def cmd_benchmark(args: argparse.Namespace) -> int:
    """Print cached benchmark comparisons against baselines."""
    benchmarks_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "benchmarks", "benchmark_results.json")
    )
    if not os.path.exists(benchmarks_path):
        print(f"Benchmark results not found at {benchmarks_path}. Run training pipeline to generate.")
        return 1

    with open(benchmarks_path, "r") as f:
        data = json.load(f)

    print("=" * 96)
    print("KETHRAVAX BENCHMARK RESULTS MATRIX")
    print(f"Host: {data['hardware']['processor']} | Device: {data['hardware']['device']}")
    print("=" * 96)
    print(
        f"{'Model':<26} {'Byte Acc':<10} {'Macro F1':<10} {'Macro IoU':<10} {'Bnd F1 (4B)':<12} {'Arch Acc':<10} {'Throughput'}"
    )
    print("-" * 96)

    for name, info in data["models"].items():
        in_dist = info["in_distribution"]
        b_acc = f"{in_dist['overall_byte_accuracy'] * 100:.1f}%"
        m_f1 = f"{in_dist['macro_f1']:.4f}"
        m_iou = f"{in_dist['macro_iou']:.4f}"
        b_f1 = f"{in_dist['boundary_f1_tol_4B']:.4f}"
        a_acc = f"{in_dist['arch_accuracy_on_code'] * 100:.1f}%"
        tp = f"{in_dist['cpu_throughput_kb_s']} KB/s"
        print(f"{name:<26} {b_acc:<10} {m_f1:<10} {m_iou:<10} {b_f1:<12} {a_acc:<10} {tp}")

    print("-" * 96)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="kethravax",
        description="Precision structural byte segmentation & ISA discovery across raw binary streams.",
    )
    parser.add_argument("-v", "--version", action="version", version=f"kethravax {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Segment a raw binary file")
    p_analyze.add_argument("file", help="Path to input binary file")
    p_analyze.add_argument("--format", choices=["text", "json"], default="text", help="Output format")
    p_analyze.add_argument("-o", "--output", help="Optional output file path")

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect byte offsets and hex dumps")
    p_inspect.add_argument("file", help="Path to input binary file")
    p_inspect.add_argument("--offset", default="0", help="Byte offset (decimal or hex like 0x1000)")
    p_inspect.add_argument("--length", default="256", help="Length in bytes to display")

    # model-info
    p_info = subparsers.add_parser("model-info", help="Display model architecture specifications")

    # benchmark
    p_bench = subparsers.add_parser("benchmark", help="Display comparative benchmark results")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "analyze":
        sys.exit(cmd_analyze(args))
    elif args.command == "inspect":
        sys.exit(cmd_inspect(args))
    elif args.command == "model-info":
        sys.exit(cmd_model_info(args))
    elif args.command == "benchmark":
        sys.exit(cmd_benchmark(args))


if __name__ == "__main__":
    main()

