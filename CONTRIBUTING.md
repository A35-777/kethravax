# Contributing to KETHRAVAX

Thank you for your interest in contributing to **KETHRAVAX**!

---

## 1. Development Principles

1. **Scientific Grounding:** All claims regarding segmentation accuracy, architecture support, or boundary precision must be substantiated with reproducible benchmark scripts.
2. **Defensive Code Quality:** Ensure all core invariants (total coverage, contiguity, no zero-length segments) are preserved in all PRs.
3. **Test-Driven:** Every new feature, parser, or baseline must include unit and regression tests.

---

## 2. Local Development Workflow

```bash
# Clone the repository
git clone https://github.com/kethravax/kethravax.git
cd kethravax

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\Activate.ps1 on Windows

# Install dependencies with test extras
pip install -e ".[dev]"

# Run tests
pytest tests/ -v
```

---

## 3. Pull Request Guidelines

- Ensure `pytest` passes with 100% success rate.
- Include appropriate documentation updates under `docs/`.
- Do not commit large binary artifacts or proprietary firmware dumps into git history.

