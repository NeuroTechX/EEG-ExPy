# EEG-ExPy Modernization

This project has been modernized to use PEP 621 (pyproject.toml) and `uv` for dependency management.

## Key Changes

- **PEP 621 Migration**: All metadata and dependencies moved from `setup.py`, `setup.cfg`, and `requirements.txt` to `pyproject.toml`.
- **Architecture Support**: Explicitly restricted to 64-bit systems (macOS ARM64/x64, Linux x64, Windows x64) in `pyproject.toml` to avoid legacy 32-bit dependency issues.
- **Ruff Linting**: Configured `ruff` for fast linting and formatting.
- **Path Centralization**: Centralized common stimuli paths in `eegnb/stimuli/__init__.py` using `pathlib.Path`.
- **Experiment Refactoring**: Refactored `VisualMindEye`, `VisualfLoc`, `VisualNaturalPRF`, and `VisualRetinotopy` for better portability and consistency.

## Usage

### Installation

```bash
uv pip install -e .
```

To install with all dependencies (streaming, stimulus presentation, etc.):

```bash
uv pip install -e ".[full]"
```

### Development

Run linting:

```bash
uvx ruff check .
```

Run tests:

```bash
uv run pytest
```

## Timing Validation

The project includes a timing validation suite to ensure stimulus markers are pushed with high precision.

### Stimulus Timing Benchmark
Measures round-trip LSL latency and jitter.
```bash
uv run python tests/test_stimulus_timing.py
```
**Latest Results (macOS):**
- Mean Round Trip Latency: ~0.14 ms
- Jitter (Std): ~0.04 ms

### Logic Execution Benchmark
Measures the internal Python overhead of the `present_stimulus` method.
```bash
uv run python tests/test_present_latency.py
```
**Latest Results:**
- VisualMindEye: ~0.04 ms
- VisualfLoc: ~0.04 ms

## Maintenance Notes

- **Build Backend**: Uses `hatchling`.
- **Python Support**: Currently restricted to `>=3.9, <3.12` due to compatibility issues with various EEG and PsychoPy dependencies (especially on macOS).
- **Direct References**: Allowed in `pyproject.toml` for some legacy Windows wheels (like `pywinhook` which was temporarily removed to ease cross-platform locking but can be added back if needed for specific Windows environments).
- **pyobjc**: Uses `~=8.5` to avoid build issues with older versions on newer Python, while remaining compatible with `psychopy`.

## New Experiments

The following experiments were recently added and refactored:
- `VisualMindEye`: Uses NSD-style natural images.
- `VisualfLoc`: Functional Localizer with multiple categories.
- `VisualRetinotopy`: Basic retinotopic mapping (bars, rings, wedges).
- `VisualNaturalPRF`: Naturalistic pRF mapping with flickering carrier images.
