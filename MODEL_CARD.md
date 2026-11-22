# Model Card: KethraSeg-Hybrid

**Model Name:** KethraSeg-Hybrid  
**Model Family:** KethraSeg  
**Architecture:** Multiscale 1D Convolutional-Recurrent Dual-Head Network  
**Version:** 0.1.0  
**License:** Apache-2.0  
**Release Date:** 2026-11-22  

---

## 1. Model Overview

**KethraSeg-Hybrid** is a learned neural sequence model trained from scratch for multi-class structural byte-stream segmentation and instruction-set architecture discovery.

It ingests raw byte tokens without requiring file headers (ELF, PE, Mach-O) or container metadata, producing contiguous structural intervals `[start, end)` annotated with category, architecture, calibrated confidence, and diagnostic metrics.

---

## 2. Model Architecture & Specifications

| Component | Specification | Description |
| :--- | :--- | :--- |
| **Input Format** | Raw bytes ($b_i \in [0, 255]$) | No text tokenization; operates directly on 8-bit machine bytes. |
| **Embedding Layer** | $256 \to 48$ dimensions | Trainable dense byte vector representation. |
| **Spatial Extractor** | Multiscale 1D Convolutions | 4 parallel branches with kernel widths 3, 5, 9, 17 (16 channels each = 64 channels total). |
| **Sequence Backbone** | Bidirectional GRU | 1 layer, hidden dimension 36 per direction (72 total). |
| **Prediction Heads** | Three Specialized Heads | 1. Structural Category Head (7 classes)<br>2. Architecture Head (9 classes)<br>3. Boundary Transition Head (1 dim, sigmoid) |
| **Parameters** | ~48,000 parameters | Highly compact, optimized for real-time CPU edge inference. |
| **Inference Target** | CPU-first (AVX2 / SSE4) | ~10-40 ms for 64 KB binary blocks on standard x86-64 CPUs. |

---

## 3. Training & Ground Truth

- **Loss Function:** Multi-task combined objective:
  $$\mathcal{L} = \mathcal{L}_{\text{cat}} + 0.5 \cdot \mathcal{L}_{\text{arch}} + 0.3 \cdot \mathcal{L}_{\text{boundary}}$$
- **Optimization:** AdamW ($\text{lr} = 0.002$, weight decay $10^{-4}$, batch size 32).
- **Hardware:** Trained entirely from scratch on AMD PRO A12-9800B CPU (No GPU required).
- **Pre-trained Weights:** None used. Initialized from scratch with Gaussian weights.

---

## 4. Evaluation Performance & Success Gates

- **Total Invariant Guarantee:** 100% of tested streams satisfy total byte coverage, contiguity, and zero overlap.
- **Boundary Localization:** Local gradient & null discontinuity snapper achieves high F1 at $\tau \in \{0, 4, 16, 32\}$ bytes.
- **Mixed Stream Robustness:** Accurately separates interleaved x86, ARM, Thumb, and data regions.

