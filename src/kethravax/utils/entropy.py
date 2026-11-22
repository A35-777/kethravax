"""Entropy, byte distribution, and statistical diagnostic utilities."""

from __future__ import annotations

import math
from typing import Dict, List, Tuple


def calculate_shannon_entropy(data: bytes) -> float:
    """Calculate the Shannon entropy of a byte sequence in bits per byte.
    
    Returns a value between 0.0 (entirely homogeneous, e.g. all 0x00)
    and 8.0 (perfectly uniform / maximum randomness).
    """
    if not data:
        return 0.0

    length = len(data)
    counts = [0] * 256
    for b in data:
        counts[b] += 1

    entropy = 0.0
    for count in counts:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)

    return float(entropy)


def calculate_sliding_entropy(
    data: bytes, window_size: int = 64, step: int = 16
) -> List[Tuple[int, float]]:
    """Compute sliding window Shannon entropy across a byte sequence.
    
    Args:
        data: Input byte sequence.
        window_size: Size of sliding window.
        step: Offset stride.
        
    Returns:
        List of (offset, entropy) pairs.
    """
    if len(data) == 0:
        return []
    if len(data) <= window_size:
        return [(0, calculate_shannon_entropy(data))]

    results = []
    for offset in range(0, len(data) - window_size + 1, step):
        window = data[offset : offset + window_size]
        results.append((offset, calculate_shannon_entropy(window)))

    # Ensure tail is covered
    if results and results[-1][0] + window_size < len(data):
        tail_offset = len(data) - window_size
        results.append((tail_offset, calculate_shannon_entropy(data[tail_offset:])))

    return results


def calculate_byte_diagnostics(data: bytes) -> Dict[str, float]:
    """Compute rich statistical diagnostics for a byte segment."""
    if not data:
        return {
            "entropy": 0.0,
            "null_ratio": 0.0,
            "printable_ratio": 0.0,
            "whitespace_ratio": 0.0,
            "high_byte_ratio": 0.0,
            "mean_byte": 0.0,
        }

    length = len(data)
    null_count = 0
    printable_count = 0
    whitespace_count = 0
    high_byte_count = 0
    byte_sum = 0
    counts = [0] * 256

    for b in data:
        byte_sum += b
        counts[b] += 1
        if b == 0:
            null_count += 1
        elif 0x20 <= b <= 0x7E:
            printable_count += 1
        elif b in (0x09, 0x0A, 0x0D):
            whitespace_count += 1

        if b >= 0x80:
            high_byte_count += 1

    # Shannon entropy
    entropy = 0.0
    for c in counts:
        if c > 0:
            p = c / length
            entropy -= p * math.log2(p)

    return {
        "entropy": round(float(entropy), 4),
        "null_ratio": round(null_count / length, 4),
        "printable_ratio": round(printable_count / length, 4),
        "whitespace_ratio": round(whitespace_count / length, 4),
        "high_byte_ratio": round(high_byte_count / length, 4),
        "mean_byte": round(byte_sum / length, 2),
    }


def find_entropy_transitions(
    data: bytes, threshold_delta: float = 1.8, window_size: int = 32
) -> List[int]:
    """Detect sharp transition points in entropy gradient."""
    if len(data) < window_size * 2:
        return []

    transitions = []
    step = window_size // 2
    for offset in range(window_size, len(data) - window_size, step):
        left_window = data[offset - window_size : offset]
        right_window = data[offset : offset + window_size]
        h_left = calculate_shannon_entropy(left_window)
        h_right = calculate_shannon_entropy(right_window)

        if abs(h_right - h_left) >= threshold_delta:
            transitions.append(offset)

    return transitions

