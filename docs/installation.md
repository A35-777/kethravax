# Installation & Setup Guide

**Project:** KETHRAVAX  
**Package:** `kethravax`  

---

## Prerequisites

- **Operating System:** Linux, macOS, or Windows 10/11 (x86_64, ARM64)
- **Python:** Version 3.9 or newer (tested on Python 3.9, 3.10, 3.11, 3.12, 3.13)
- **Hardware:** Designed CPU-first. Runs comfortably on modest hardware (e.g. 4 CPU cores, 4-8 GB RAM). GPU acceleration is optional and automatically utilized if CUDA is available.

---

## 1. Quick Installation via pip

Install the package directly into your virtual environment:

```bash
# Clone the repository
git clone https://github.com/kethravax/kethravax.git
cd kethravax

# Create and activate a clean virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate
# On Windows PowerShell:
.venv\Scripts\Activate.ps1

# Install in editable development mode
pip install -e .
```

Verify the installation:

```bash
kethravax --version
# Expected: kethravax 0.1.0
```

---

## 2. Core Dependencies

Kethravax maintains a lean dependency tree:

- `torch >= 2.0.0`: Tensor operations and neural inference engines (CPU or CUDA).
- `numpy >= 1.20.0`: Efficient byte array manipulation and diagnostic metrics.
- `scikit-learn >= 1.0.0`: Classical ML baseline models and evaluation routines.
- `pefile >= 2023.2.7`: Structural metadata and symbol extraction for Windows PE binaries.

---

## 3. Running Pre-Flight Diagnostics

Validate that your environment is fully configured and all core units pass:

```bash
pytest tests/ -v
```

