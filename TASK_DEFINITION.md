# Task Definition: Multi-Class Structural Byte-Stream Segmentation

**Document Version:** 1.0.0  
**Project:** KETHRAVAX  
**Classification:** Core Machine Learning Problem Formulation  
**Date:** 2026-11-22  

---

## 1. Problem Formulation

Let a raw binary stream $B$ of length $N$ bytes be represented as an indexed sequence:
$$B = \langle b_0, b_1, b_2, \dots, b_{N-1} \rangle \quad \text{where } b_i \in \{0, 1, \dots, 255\}$$

Unlike conventional file classification which maps $B \to y \in \mathcal{Y}_{\text{file}}$, or instruction-level disassembly which assumes known valid code, **Multi-Class Structural Byte-Stream Segmentation** maps $B$ into an ordered sequence of contiguous, non-overlapping segments:
$$\mathcal{S} = \langle S_0, S_1, \dots, S_{M-1} \rangle$$

Each segment $S_k$ is a tuple:
$$S_k = \Big( \text{start}_k, \, \text{end}_k, \, \mathcal{C}_k, \, \mathcal{A}_k, \, c_k, \, \mathcal{D}_k \Big)$$

where:
1. $\text{start}_k \in \mathbb{N}_0$ is the inclusive starting byte offset.
2. $\text{end}_k \in \mathbb{N}_0$ is the exclusive ending byte offset ($\text{start}_k < \text{end}_k$).
3. $\mathcal{C}_k \in \mathcal{T}_{\text{structural}}$ is the primary structural category from the taxonomy.
4. $\mathcal{A}_k \in \mathcal{T}_{\text{arch}} \cup \{\text{NONE}\}$ is the detected architecture (defined only when $\mathcal{C}_k = \text{CODE}$).
5. $c_k \in [0.0, 1.0]$ is the calibrated model confidence.
6. $\mathcal{D}_k$ is a diagnostic property dictionary containing local entropy ($H_k$), byte distribution metrics, and alternative candidate predictions.

### Mandatory Invariants:
1. **Total Coverage Invariant:**
   $$\text{start}_0 = 0, \quad \text{end}_{M-1} = N, \quad \text{and} \quad \forall k \in [0, M-2]: \ \text{end}_k = \text{start}_{k+1}$$
   *Not a single byte of input may be lost, omitted, duplicated, or reordered.*
2. **Contiguity Invariant:**
   $$\forall k: \ \text{end}_k > \text{start}_k$$
   *Zero-length segments are strictly prohibited.*
3. **Disjointness Invariant:**
   $$\forall j \ne k: \ [\text{start}_j, \text{end}_j) \cap [\text{start}_k, \text{end}_k) = \emptyset$$

---

## 2. Input and Operational Conditions

The system must operate successfully under the following operational conditions:
1. **Headerless Streams:** The input stream may have all headers (ELF, PE, Mach-O, Zip, Tar) stripped, corrupted, or absent.
2. **Arbitrary Offset Ingestion:** The stream may begin at an arbitrary byte offset within an executable or data structure.
3. **Mixed Payloads:** The stream may contain contiguous sub-sequences belonging to different structural categories (e.g., x86-64 code followed by alignment bytes, a jump table, an ASCII string pool, and a zlib compressed payload).
4. **Mixed Architectures:** The stream may transition between distinct instruction architectures (e.g., ARM32 ARM mode switching to Thumb mode, or mixed firmware containing both host code and co-processor code).
5. **No File Execution:** The analysis must be strictly static and observational; input bytes must never be executed under any circumstances.

---

## 3. Desired Segment Properties & Granularity

- **Minimum Segment Resolution:** The system must detect structured segments down to 16 bytes (e.g. short alignment padding or small jump tables).
- **Boundary Localization:** Transition offsets between structural classes must be localized within tight byte tolerance ($\tau = 0, 4, 16, 32$ bytes).
- **Calibrated Uncertainty:** Regions with insufficient semantic signal (e.g. short, ambiguous byte sequences that could equally be random data or rare opcodes) must be explicitly flagged with lower confidence or assigned the `UNKNOWN_AMBIGUOUS` label rather than forcing a false positive.

