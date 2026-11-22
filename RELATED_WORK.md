# Related Work: Foundations of Binary Analysis, Disassembly, and Neural Sequence Modeling

**Document Version:** 1.0.0  
**Project:** KETHRAVAX  
**Classification:** Literature Survey & Theoretical Grounding  
**Date:** 2026-11-22  

---

## 1. Introduction

The discipline of binary analysis has evolved across three major technological epochs:
1. **Rule-Based & Heuristic Parsing (1990s–2000s):** Tools relying strictly on file-format specifications (COFF, ELF, PE) and recursive/linear sweep disassembly (e.g. IDA Pro).
2. **Statistical & Corpus Analysis (2010s):** Statistical n-gram models, entropy analysis, and machine-learning classifiers for architecture detection and basic code/data classification (e.g. ELISA, cpu_rec).
3. **Deep Neural & Sequence Representation (2020s–Present):** Deep learning applied to raw bytes and instruction streams, incorporating Transformers, Graph Neural Networks, and Temporal Convolutions (e.g. Magika, XDA, DeepDi, Remigio et al.).

KETHRAVAX is situated at the intersection of deep sequence modeling, digital forensics, and binary reverse engineering.

---

## 2. Code/Data Boundary Detection in Raw Streams

The fundamental challenge of distinguishing code from data stems from von Neumann architecture principles: both executable instructions and data reside in the same physical address space and are encoded as sequences of bytes.

In CISC architectures (notably x86 and x86-64), instructions are variable-length (1 to 15 bytes) and unaligned:
- Any arbitrary sequence of data bytes can theoretically be decoded as valid x86 instructions.
- A disassembler that mistakenly begins disassembling in a data section will decode "phantom instructions" and can remain desynchronized for dozens of instructions before re-synchronizing.

In RISC architectures (ARM, MIPS, RISC-V), instructions are fixed-length (usually 4 bytes) and aligned:
- While alignment reduces desynchronization, literal pools and jump tables are routinely interleaved directly inside `.text` sections to accommodate PC-relative load instructions with limited immediate offsets (e.g., ARM `LDR r0, [pc, #offset]`).
- Without symbol tables or relocation entries, disassemblers decode these literal pools as nonsensical instructions.

### The Evolution from ELISA to Recurrent Models
- **Polino et al. (ELISA):** Formulated code/data separation as a sequence tagging problem using Linear-Chain Conditional Random Fields (CRFs). CRFs model the conditional distribution $P(Y \mid X)$ over label sequence $Y$ given input features $X$, incorporating transition potentials between adjacent labels:
  $$P(Y \mid X) = \frac{1}{Z(X)} \exp\left( \sum_{t=1}^T \sum_k \lambda_k f_k(y_t, y_{t-1}, X, t) \right)$$
  While mathematically principled, CRFs require heavy feature engineering (e.g. testing whether 4 bytes decode to valid instructions in candidate ISAs) and incur $O(T \cdot |Y|^2)$ computational complexity.
- **Remigio et al. (IWSEC 2023):** Replaced the hand-engineered CRF with a Bidirectional Long Short-Term Memory (BiLSTM) network. BiLSTMs learn dense vector representations directly from sequential inputs, maintaining forward hidden state $\overrightarrow{h}_t$ and backward hidden state $\overleftarrow{h}_t$:
  $$h_t = [\overrightarrow{h}_t \,\|\, \overleftarrow{h}_t]$$
  This captures bidirectional context: a function prologue (e.g. `push rbp; mov rbp, rsp`) informs the classification of subsequent instructions, while an upcoming epilogue (`pop rbp; ret`) prevents premature classification transitions.

---

## 3. Byte-Level Neural Representations & Architectures

Modeling raw bytes presents unique engineering and theoretical considerations:
1. **Vocabulary Size:** The byte alphabet is compact ($|\Sigma| = 256$, ranging from `0x00` to `0xFF`). Unlike natural language processing with open vocabularies, out-of-vocabulary (OOV) tokens do not exist.
2. **Sequence Length:** Binary files are large (kilobytes to hundreds of megabytes). Standard Transformer self-attention with $O(N^2)$ memory and compute complexity cannot process long raw byte sequences without extreme subsampling or memory exhaustion.
3. **Local vs Long-Range Dependencies:**
   - *Local dependencies:* Opcodes and their immediate operands span 1 to 15 bytes.
   - *Medium-range dependencies:* Basic blocks and function loops span 16 to 512 bytes.
   - *Long-range dependencies:* Section layouts, jump tables, and string references span kilobytes to megabytes.

### Convolutional vs Recurrent Architectures
- **Temporal Convolutional Networks (TCNs):** Use 1D dilated convolutions with receptive field growing exponentially with layer depth:
  $$\text{RF} = 1 + \sum_{l=0}^{L-1} (K - 1) \cdot d_l$$
  TCNs process sequences in parallel during training (unlike RNNs which require sequential backpropagation through time), consume predictable constant memory during inference, and excel at capturing multi-scale n-gram patterns.
- **BiLSTMs:** Superior at remembering persistent state across arbitrary sequence distances, but suffer from sequential execution latency and boundary transition smearing.
- **Hybrid Convolutive-Recurrent Models:** KETHRAVAX investigates a hybrid architecture where multiscale 1D convolutions extract local byte features, feeding into a lightweight bidirectional sequence backbone for contextual consistency.

---

## 4. Boundary Refinement and Structural Decoding

A recurring defect in neural sequence segmentation is **boundary jitter**. When a neural model operates on windowed strides (e.g. stride $S = 16$ or $32$), the predicted label transition can be displaced from the true byte-level transition by several strides.

Prior solutions either accepted coarse boundaries (Remigio et al.) or used expensive heuristic sweeps.

KETHRAVAX integrates a two-stage boundary refinement formulation:
1. **Macro Sequence Tagging:** Predicts structural category probabilities across strided sequence windows.
2. **Boundary-Snapping Head:** A specialized sub-network and transition detector that inspects local byte gradients, entropy variance, and null/padding discontinuities in a narrow window around detected transitions, snapping boundaries to exact byte offsets.

