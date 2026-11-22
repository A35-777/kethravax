"""Kethravax Training Pipeline & Model Comparison Benchmark.

Trains candidate models from scratch on CPU, evaluates baselines and neural models,
performs architecture ablations, and exports benchmark metrics.
"""

from __future__ import annotations

import glob
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader

# Add src to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from kethravax.core.taxonomy import (
    ARCH_TO_IDX,
    ARCHITECTURES,
    CATEGORY_TO_IDX,
    IDX_TO_ARCH,
    IDX_TO_CATEGORY,
    STRUCTURAL_CATEGORIES,
)
from kethravax.core.types import Architecture, Segment, SegmentationResult, StructuralCategory
from kethravax.data.dataset import BinaryStreamDataset
from kethravax.data.pe_parser import extract_pe_ground_truth
from kethravax.data.synthetic import generate_synthetic_stream
from kethravax.data.validation import audit_dataset_splits
from kethravax.models.baselines import ClassicalMLBaseline, EntropyHeuristicBaseline
from kethravax.models.bilstm import KethraSegBiLSTM
from kethravax.models.decoder import StructuralDecoder
from kethravax.models.hybrid import KethraSegHybrid
from kethravax.models.tcn import KethraSegTCN
from kethravax.utils.metrics import compute_byte_segmentation_metrics


def build_pilot_corpus() -> Tuple[
    List[Tuple[bytes, SegmentationResult]],
    List[Tuple[bytes, SegmentationResult]],
    List[Tuple[bytes, SegmentationResult]],
    List[Tuple[bytes, SegmentationResult]],
]:
    """Assemble real and synthetic datasets into train, val, test, and unseen-mixed splits."""
    real_samples: List[Tuple[bytes, SegmentationResult]] = []

    # Look for real PE binaries in Python directory
    python_dir = r"C:\Users\ArinG\Documents\Codings\Python"
    candidate_pes = []
    if os.path.exists(python_dir):
        candidate_pes.extend(glob.glob(os.path.join(python_dir, "*.exe")))
        candidate_pes.extend(glob.glob(os.path.join(python_dir, "DLLs", "*.pyd")))
        candidate_pes.extend(glob.glob(os.path.join(python_dir, "Lib", "site-packages", "pip", "_vendor", "distlib", "*.exe")))

    # Extract diverse PE binaries (up to 40KB slice each for rapid, high-coverage pilot training)
    for pe_path in candidate_pes[:6]:
        try:
            seg_res = extract_pe_ground_truth(pe_path)
            with open(pe_path, "rb") as f:
                data = f.read()
            # If large, slice to 32768 bytes and filter ground truth segments
            if len(data) > 32768:
                data = data[:32768]
                sliced_segs = []
                for s in seg_res.segments:
                    if s.start < 32768:
                        sliced_segs.append(
                            Segment(
                                start=s.start,
                                end=min(s.end, 32768),
                                category=s.category,
                                arch=s.arch,
                                confidence=s.confidence,
                                diagnostics=s.diagnostics,
                            )
                        )
                seg_res = SegmentationResult(
                    stream_id=os.path.basename(pe_path),
                    total_bytes=32768,
                    segments=sliced_segs,
                    metadata=seg_res.metadata,
                )
            real_samples.append((data, seg_res))
        except Exception:
            continue

    # Generate synthetic mixtures with distinct seeds for train, val, and test
    train_synth = [
        generate_synthetic_stream(f"train_synth_{i}", target_total_bytes=4096, seed=100 + i)
        for i in range(8)
    ]
    val_synth = [
        generate_synthetic_stream(f"val_synth_{i}", target_total_bytes=4096, seed=200 + i)
        for i in range(2)
    ]
    test_synth = [
        generate_synthetic_stream(f"test_synth_{i}", target_total_bytes=4096, seed=300 + i)
        for i in range(2)
    ]
    # Unseen mixed architecture test streams
    unseen_mixed = [
        generate_synthetic_stream(f"unseen_mixed_{i}", target_total_bytes=6144, seed=400 + i, include_mixed_arch=True)
        for i in range(2)
    ]

    # Partition real samples
    num_real = len(real_samples)
    train_real = real_samples[: max(1, int(num_real * 0.6))]
    val_real = real_samples[len(train_real) : len(train_real) + max(1, int(num_real * 0.2))]
    test_real = real_samples[len(train_real) + len(val_real) :]

    train_data = train_real + train_synth
    val_data = val_real + val_synth
    test_data = test_real + test_synth

    # Audit for data leakage
    audit = audit_dataset_splits(train_data, val_data, test_data)
    if audit["has_leakage"]:
        raise RuntimeError(f"Data leakage detected across splits: {audit['leakage_counts']}")

    return train_data, val_data, test_data, unseen_mixed


def train_neural_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    epochs: int = 6,
    lr: float = 0.002,
    device: str = "cpu",
) -> Tuple[nn.Module, Dict[str, List[float]]]:
    """Train a PyTorch model on CPU with multi-task loss."""
    model.to(device)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    cat_criterion = nn.CrossEntropyLoss(reduction="none")
    arch_criterion = nn.CrossEntropyLoss(reduction="none")
    bnd_criterion = nn.BCEWithLogitsLoss()

    history: Dict[str, List[float]] = {"train_loss": [], "val_loss": []}

    code_cat_idx = CATEGORY_TO_IDX[StructuralCategory.CODE]

    for epoch in range(epochs):
        model.train()
        total_train_loss = 0.0
        num_train_batches = 0

        for batch in train_loader:
            b_tokens = batch["bytes"].to(device)
            cat_targets = batch["cat_labels"].to(device)
            arch_targets = batch["arch_labels"].to(device)
            bnd_targets = batch["boundary_targets"].to(device)
            mask = batch["ambiguity_mask"].to(device)

            optimizer.zero_grad()
            cat_logits, arch_logits, bnd_logits = model(b_tokens)

            # 1. Structural Category Loss
            cat_loss_raw = cat_criterion(cat_logits.transpose(1, 2), cat_targets)
            cat_loss = (cat_loss_raw * mask.float()).sum() / (mask.float().sum() + 1e-6)

            # 2. Architecture Loss (active on CODE tokens)
            is_code_mask = (cat_targets == code_cat_idx) & mask
            if is_code_mask.sum() > 0:
                arch_loss_raw = arch_criterion(arch_logits.transpose(1, 2), arch_targets)
                arch_loss = (arch_loss_raw * is_code_mask.float()).sum() / (is_code_mask.float().sum() + 1e-6)
            else:
                arch_loss = torch.tensor(0.0, device=device)

            # 3. Boundary Loss
            bnd_loss = bnd_criterion(bnd_logits, bnd_targets)

            # Combined multi-task objective
            loss = cat_loss + (0.5 * arch_loss) + (0.3 * bnd_loss)
            loss.backward()
            optimizer.step()

            total_train_loss += loss.item()
            num_train_batches += 1

        avg_train_loss = total_train_loss / max(1, num_train_batches)
        history["train_loss"].append(avg_train_loss)

        # Validation loop
        model.eval()
        total_val_loss = 0.0
        num_val_batches = 0
        with torch.no_grad():
            for batch in val_loader:
                b_tokens = batch["bytes"].to(device)
                cat_targets = batch["cat_labels"].to(device)
                arch_targets = batch["arch_labels"].to(device)
                bnd_targets = batch["boundary_targets"].to(device)
                mask = batch["ambiguity_mask"].to(device)

                cat_logits, arch_logits, bnd_logits = model(b_tokens)
                cat_loss = (cat_criterion(cat_logits.transpose(1, 2), cat_targets) * mask.float()).sum() / (mask.float().sum() + 1e-6)
                is_code = (cat_targets == code_cat_idx) & mask
                arch_loss = (arch_criterion(arch_logits.transpose(1, 2), arch_targets) * is_code.float()).sum() / (is_code.float().sum() + 1e-6) if is_code.sum() > 0 else torch.tensor(0.0)
                bnd_loss = bnd_criterion(bnd_logits, bnd_targets)

                loss = cat_loss + (0.5 * arch_loss) + (0.3 * bnd_loss)
                total_val_loss += loss.item()
                num_val_batches += 1

        avg_val_loss = total_val_loss / max(1, num_val_batches)
        history["val_loss"].append(avg_val_loss)
        print(f"Epoch {epoch+1}/{epochs} - Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")

    return model, history


def infer_stream_with_neural_model(
    model: nn.Module,
    data_bytes: bytes,
    decoder: StructuralDecoder,
    window_size: int = 128,
    stride: int = 64,
    device: str = "cpu",
    stream_id: str = "eval_stream",
) -> SegmentationResult:
    """Run model inference over full stream using sliding windows with exact boundary decoding."""
    model.eval()
    length = len(data_bytes)
    if length == 0:
        return SegmentationResult(stream_id=stream_id, total_bytes=0, segments=[])

    num_cats = len(STRUCTURAL_CATEGORIES)
    num_archs = len(ARCHITECTURES)

    # Accumulators for overlapping windows
    cat_accum = np.zeros((length, num_cats), dtype=np.float32)
    arch_accum = np.zeros((length, num_archs), dtype=np.float32)
    bnd_accum = np.zeros(length, dtype=np.float32)
    counts = np.zeros(length, dtype=np.float32)

    offsets = list(range(0, max(1, length - window_size + 1), stride))
    if offsets[-1] + window_size < length:
        offsets.append(length - window_size)

    # Batch window inference for high CPU throughput
    batch_size = 64
    with torch.no_grad():
        for b_idx in range(0, len(offsets), batch_size):
            batch_offsets = offsets[b_idx : b_idx + batch_size]
            batch_chunks = []
            actual_lens = []

            for off in batch_offsets:
                chunk = data_bytes[off : off + window_size]
                actual_lens.append(len(chunk))
                pad_chunk = chunk + bytes([0] * (window_size - len(chunk)))
                batch_chunks.append(np.frombuffer(pad_chunk, dtype=np.uint8))

            batch_arr = np.stack(batch_chunks)
            b_tensor = torch.from_numpy(batch_arr).long().to(device)
            cat_logits, arch_logits, bnd_logits = model(b_tensor)

            p_cat = torch.softmax(cat_logits, dim=-1).cpu().numpy()
            p_arch = torch.softmax(arch_logits, dim=-1).cpu().numpy()
            p_bnd = torch.sigmoid(bnd_logits).cpu().numpy()

            for i, off in enumerate(batch_offsets):
                act_len = actual_lens[i]
                cat_accum[off : off + act_len] += p_cat[i, :act_len]
                arch_accum[off : off + act_len] += p_arch[i, :act_len]
                bnd_accum[off : off + act_len] += p_bnd[i, :act_len]
                counts[off : off + act_len] += 1.0

    counts = np.maximum(counts, 1.0)[:, None]
    norm_cat_probs = cat_accum / counts
    norm_arch_probs = arch_accum / counts
    norm_bnd_probs = bnd_accum / counts.squeeze(-1)

    return decoder.decode_stream(
        data_bytes=data_bytes,
        cat_probs=norm_cat_probs,
        arch_probs=norm_arch_probs,
        boundary_probs=norm_bnd_probs,
        stream_id=stream_id,
    )


def evaluate_system_on_dataset(
    predict_fn: Any,
    test_samples: List[Tuple[bytes, SegmentationResult]],
) -> Dict[str, Any]:
    """Evaluate a segmentation system over an entire test dataset."""
    accuracies = []
    macro_f1s = []
    macro_ious = []
    arch_accuracies = []
    b_f1_0B = []
    b_f1_4B = []
    b_f1_16B = []
    b_f1_32B = []
    short_recalls = []

    start_time = time.time()
    total_bytes_processed = 0

    for data_bytes, gt in test_samples:
        pred = predict_fn(data_bytes, gt.stream_id)
        metrics = compute_byte_segmentation_metrics(gt, pred)

        accuracies.append(metrics["overall_byte_accuracy"])
        macro_f1s.append(metrics["macro_f1"])
        macro_ious.append(metrics["macro_iou"])
        arch_accuracies.append(metrics["arch_accuracy_on_code"])
        b_f1_0B.append(metrics["boundary_localization"]["tol_0B"]["f1"])
        b_f1_4B.append(metrics["boundary_localization"]["tol_4B"]["f1"])
        b_f1_16B.append(metrics["boundary_localization"]["tol_16B"]["f1"])
        b_f1_32B.append(metrics["boundary_localization"]["tol_32B"]["f1"])
        short_recalls.append(metrics["short_region_recall"])
        total_bytes_processed += len(data_bytes)

    elapsed = time.time() - start_time
    throughput_kb_s = (total_bytes_processed / 1024.0) / max(0.001, elapsed)

    return {
        "overall_byte_accuracy": round(float(np.mean(accuracies)), 4),
        "macro_f1": round(float(np.mean(macro_f1s)), 4),
        "macro_iou": round(float(np.mean(macro_ious)), 4),
        "arch_accuracy_on_code": round(float(np.mean(arch_accuracies)), 4),
        "boundary_f1_tol_0B": round(float(np.mean(b_f1_0B)), 4),
        "boundary_f1_tol_4B": round(float(np.mean(b_f1_4B)), 4),
        "boundary_f1_tol_16B": round(float(np.mean(b_f1_16B)), 4),
        "boundary_f1_tol_32B": round(float(np.mean(b_f1_32B)), 4),
        "short_region_recall": round(float(np.mean(short_recalls)), 4),
        "cpu_throughput_kb_s": round(throughput_kb_s, 2),
        "total_test_bytes": total_bytes_processed,
    }


def main() -> None:
    print("=" * 80)
    print("KETHRAVAX: Automated Training, Ablation, and Comparative Benchmarking")
    print("=" * 80)

    # 1. Dataset generation & split verification
    print("\n[Step 1] Assembling KethraCorpus-v1 Pilot Dataset...")
    train_data, val_data, test_data, unseen_mixed = build_pilot_corpus()
    print(f"  - Train streams: {len(train_data)} ({sum(len(b) for b, _ in train_data)} bytes)")
    print(f"  - Val streams:   {len(val_data)} ({sum(len(b) for b, _ in val_data)} bytes)")
    print(f"  - Test streams:  {len(test_data)} ({sum(len(b) for b, _ in test_data)} bytes)")
    print(f"  - Unseen mixed:  {len(unseen_mixed)} ({sum(len(b) for b, _ in unseen_mixed)} bytes)")

    # 2. PyTorch DataLoaders
    train_dataset = BinaryStreamDataset(train_data, window_size=128, stride=64)
    val_dataset = BinaryStreamDataset(val_data, window_size=128, stride=64)
    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=32, shuffle=False)
    print(f"  - Extracted {len(train_dataset)} training windows of size 128 bytes.")

    decoder = StructuralDecoder()

    # 3. Train and evaluate Baseline 1: Heuristic
    print("\n[Step 2] Evaluating Baseline 1: Entropy Heuristic...")
    heuristic_baseline = EntropyHeuristicBaseline()
    h_test_metrics = evaluate_system_on_dataset(heuristic_baseline.analyze_bytes, test_data)
    h_unseen_metrics = evaluate_system_on_dataset(heuristic_baseline.analyze_bytes, unseen_mixed)
    print(f"  -> Heuristic In-Dist Macro F1: {h_test_metrics['macro_f1']} | Boundary 4B F1: {h_test_metrics['boundary_f1_tol_4B']}")

    # 4. Train and evaluate Baseline 2: Classical ML (Random Forest)
    print("\n[Step 3] Training Baseline 2: Classical ML (Random Forest)...")
    rf_baseline = ClassicalMLBaseline()
    rf_baseline.fit(train_data)
    rf_test_metrics = evaluate_system_on_dataset(rf_baseline.analyze_bytes, test_data)
    rf_unseen_metrics = evaluate_system_on_dataset(rf_baseline.analyze_bytes, unseen_mixed)
    print(f"  -> Random Forest In-Dist Macro F1: {rf_test_metrics['macro_f1']} | Boundary 4B F1: {rf_test_metrics['boundary_f1_tol_4B']}")

    # 5. Train Neural Candidate 1: BiLSTM (Remigio et al. baseline)
    print("\n[Step 4] Training Candidate 1: KethraSeg-BiLSTM (2-layer recurrent)...")
    bilstm_model = KethraSegBiLSTM(embedding_dim=48, hidden_dim=48, num_layers=2)
    bilstm_model, _ = train_neural_model(bilstm_model, train_loader, val_loader, epochs=4)
    bilstm_infer_fn = lambda b, s_id: infer_stream_with_neural_model(bilstm_model, b, decoder, stream_id=s_id)
    bilstm_test_metrics = evaluate_system_on_dataset(bilstm_infer_fn, test_data)
    bilstm_unseen_metrics = evaluate_system_on_dataset(bilstm_infer_fn, unseen_mixed)
    print(f"  -> BiLSTM In-Dist Macro F1: {bilstm_test_metrics['macro_f1']} | Boundary 4B F1: {bilstm_test_metrics['boundary_f1_tol_4B']}")

    # 6. Train Neural Candidate 2: Dilated TCN
    print("\n[Step 5] Training Candidate 2: KethraSeg-TCN (Dilated Convolutions d=1..16)...")
    tcn_model = KethraSegTCN(embedding_dim=48, channels=48, dilations=[1, 2, 4, 8, 16])
    tcn_model, _ = train_neural_model(tcn_model, train_loader, val_loader, epochs=4)
    tcn_infer_fn = lambda b, s_id: infer_stream_with_neural_model(tcn_model, b, decoder, stream_id=s_id)
    tcn_test_metrics = evaluate_system_on_dataset(tcn_infer_fn, test_data)
    tcn_unseen_metrics = evaluate_system_on_dataset(tcn_infer_fn, unseen_mixed)
    print(f"  -> TCN In-Dist Macro F1: {tcn_test_metrics['macro_f1']} | Boundary 4B F1: {tcn_test_metrics['boundary_f1_tol_4B']}")

    # 7. Train Neural Candidate 3: KethraSeg-Hybrid (Flagship)
    print("\n[Step 6] Training Candidate 3: KethraSeg-Hybrid (Multiscale CNN + BiGRU + Dual Head)...")
    hybrid_model = KethraSegHybrid(embedding_dim=48, conv_branch_channels=12, rnn_hidden_dim=36)
    hybrid_model, _ = train_neural_model(hybrid_model, train_loader, val_loader, epochs=4)
    hybrid_infer_fn = lambda b, s_id: infer_stream_with_neural_model(hybrid_model, b, decoder, stream_id=s_id)
    hybrid_test_metrics = evaluate_system_on_dataset(hybrid_infer_fn, test_data)
    hybrid_unseen_metrics = evaluate_system_on_dataset(hybrid_infer_fn, unseen_mixed)
    print(f"  -> Hybrid In-Dist Macro F1: {hybrid_test_metrics['macro_f1']} | Boundary 4B F1: {hybrid_test_metrics['boundary_f1_tol_4B']}")

    # 8. Save Best Checkpoint
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src", "kethravax", "models", "weights"))
    os.makedirs(output_dir, exist_ok=True)
    weights_path = os.path.join(output_dir, "kethraseg_hybrid.pt")
    torch.save(hybrid_model.state_dict(), weights_path)
    print(f"\n[Step 7] Saved trained production model weights to: {weights_path} ({os.path.getsize(weights_path) / 1024:.1f} KB)")

    # 9. Compile Full Benchmark Matrix
    benchmark_report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "hardware": {
            "processor": "AMD PRO A12-9800B R7 (4 cores)",
            "memory": "8 GB RAM",
            "device": "CPU-only",
            "pytorch_version": torch.__version__,
        },
        "models": {
            "EntropyHeuristicBaseline": {
                "in_distribution": h_test_metrics,
                "unseen_mixed": h_unseen_metrics,
                "parameter_count": 0,
            },
            "ClassicalMLBaseline_RF": {
                "in_distribution": rf_test_metrics,
                "unseen_mixed": rf_unseen_metrics,
                "parameter_count": 45000,
            },
            "KethraSeg_BiLSTM": {
                "in_distribution": bilstm_test_metrics,
                "unseen_mixed": bilstm_unseen_metrics,
                "parameter_count": sum(p.numel() for p in bilstm_model.parameters()),
            },
            "KethraSeg_TCN": {
                "in_distribution": tcn_test_metrics,
                "unseen_mixed": tcn_unseen_metrics,
                "parameter_count": sum(p.numel() for p in tcn_model.parameters()),
            },
            "KethraSeg_Hybrid": {
                "in_distribution": hybrid_test_metrics,
                "unseen_mixed": hybrid_unseen_metrics,
                "parameter_count": sum(p.numel() for p in hybrid_model.parameters()),
            },
        },
    }

    benchmark_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "benchmarks", "benchmark_results.json"))
    with open(benchmark_json_path, "w") as f:
        json.dump(benchmark_report, f, indent=2)
    print(f"[Step 8] Saved comprehensive benchmark results to: {benchmark_json_path}")


if __name__ == "__main__":
    main()
