# qgrav v0.7.0 — Quantum Gravimeter R&D Platform

A **software-first research workbench** for atom interferometer gravimetry when lab hardware is unavailable. Instead of making false hardware claims, `qgrav` provides a complete pipeline from simulation through analysis to reproducible reporting.

**Author:** Aditya Prakash | **License:** MIT | **Python:** >= 3.9

---

## What it does

| Stage | Description |
|-------|-------------|
| **Simulate** | AISim-backed atom interferometry: Rabi scans, Mach-Zehnder phase scans, gravity sweeps, vibration sensitivity sweeps |
| **Generate** | Virtual interferometer I/Q data with known truth displacement for algorithm benchmarking |
| **Ingest** | Real gravimetry time-series from `.ggp`, `.zip`, directory, or CSV (superconducting gravimeter residuals) |
| **Analyze** | PSD, overlapping Allan deviation (custom + AllanTools backends), noise type classification, shot-noise sensitivity |
| **Validate** | Published reference comparison (Freier 2016, Menoret 2018, etc.), systematic effects estimation, backend cross-checks |
| **Report** | Auto-generated HTML reports with plots, metrics, systematics tables, and full config snapshots |
| **GUI** | tkinter desktop app for interactive config editing, pipeline execution, and plot viewing |

---

## Quick start

### Install

```bash
git clone https://github.com/adityagit94/Quantum-Gravitometer.git
cd Quantum-Gravitometer

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -U pip
pip install -e .
```

### Run your first pipeline

```bash
# Synthetic virtual interferometer (no external data needed)
qgrav run --config configs/example.yaml
```

This creates a timestamped folder under `runs/` — open `report.html` in your browser for the full results.

### More examples

```bash
# AISim Rabi scan
qgrav run --config configs/example_aisim.yaml

# AISim Mach-Zehnder phase scan
qgrav run --config configs/example_aisim_phase_scan.yaml

# AISim gravity sweep (hybrid: AISim pulse transfer + gravimeter phase law)
qgrav run --config configs/example_aisim_gravity_sweep.yaml

# AISim vibration sensitivity sweep
qgrav run --config configs/example_aisim_vibration_sweep.yaml

# Real gravimetry (requires data in data/raw/sg_sample/)
qgrav run --config configs/example_real_gravity.yaml
```

### Launch the GUI

```bash
qgrav gui
# or pre-load a config:
qgrav gui --config configs/example.yaml
```

### Convert GGP to CSV

```bash
qgrav convert-ggp --source data/raw/sg_sample --station ap046 --out ap046.csv
```

---

## Bench modes

### `virtual`
Synthetic interferometer I/Q data with configurable displacement signals, noise, and drift. Known ground truth enables algorithm accuracy measurement (RMSE, MAE, SNR, PSD correlation).

### `real`
Real interferometer-style CSV input with `I_meas`, `Q_meas` columns and optional `x_true` for validation.

### `real_gravity`
Real gravimetry time-series ingestion supporting `.ggp` files, `.zip` archives, directories of `.ggp` files, or pre-converted CSV. Includes gap detection, longest-contiguous-segment analysis, and dropped-row tracking.

---

## Pipeline outputs

Each `qgrav run` creates a timestamped folder:

```
runs/<name>_<timestamp>/
    config_used.yaml          # exact config snapshot for reproducibility
    data.npz                  # all arrays (time, signals, Allan taus, ADEV, etc.)
    metrics.json              # all computed metrics, sensitivity, noise ID, systematics
    SUMMARY.md                # human-readable summary
    report.html               # full HTML report with plots and tables
    plots/
        dashboard.png         # 2x2 overview
        allan.png             # Allan deviation with noise type annotation
        psd.png               # power spectral density
        ...
```

### What's in metrics.json

- Error statistics (RMSE, MAE, bias, SNR) with baseline vs. improved comparison
- PSD via periodogram or Welch method
- Overlapping Allan deviation with backend cross-validation
- **Noise type identification** — slope classification (white PM/FM, flicker PM/FM, random walk FM)
- **Allan minimum** — optimal averaging time
- **Shot-noise sensitivity** — `1/(C * k_eff * T^2 * sqrt(N/T_cycle))` in m/s^2/sqrt(Hz) and uGal/sqrt(Hz)
- **Systematic effects** — gravity gradient shift, Coriolis shift (order-of-magnitude estimates)
- Gap report (for real gravity data)

---

## Scientific features

### Shot-noise sensitivity
Computes the quantum projection noise limit for atom interferometer gravimeters:

```
delta_g = 1 / (C * k_eff * T^2 * sqrt(N / T_cycle))
```

Available as `shot_noise_sensitivity_m_s2_per_sqrt_hz()` and `sensitivity_ugal_per_sqrt_hz()` in `qgrav.physics`.

### Noise type identification
Fits the log-log slope of Allan deviation curves and classifies into standard noise types:

| Slope | Noise type |
|-------|-----------|
| -1.0 | White phase modulation |
| -0.75 | Flicker phase modulation |
| -0.5 | White frequency modulation |
| -0.25 | Flicker frequency modulation |
| +0.5 | Random walk frequency modulation |

### Systematic effects
Order-of-magnitude estimates (clearly documented as **not** included in AISim simulation):
- **Gravity gradient** — vertical free-air gradient effect during free fall
- **Coriolis** — Earth rotation coupling with horizontal atomic velocity

### Published references
Frozen registry of benchmark values with DOI links for validation:
- Freier et al. (2016) — gravimetric sensitivity
- Menoret et al. (2018) — absolute accuracy
- Hinderer, Crossley & Warburton (2007) — SG noise floor
- Peters, Chung & Chu (2001) — MZ fringe visibility

---

## Batch processing

For multi-station analysis with real gravimetry data:

```bash
# Scan all stations, output quality metrics to CSV
python scripts/batch_scan_stations.py --source path/to/ggp_data --output results.csv

# Overlaid Allan/PSD comparison plot across stations
python scripts/multi_station_comparison.py --source path/to/ggp_data --output comparison.png
```

---

## AISim gravimeter studies

Three thesis/report-quality simulation studies:

| Config | Study |
|--------|-------|
| `example_aisim_phase_scan.yaml` | Full three-pulse Mach-Zehnder phase scan |
| `example_aisim_gravity_sweep.yaml` | Hybrid gravity sweep (AISim pulse transfer + gravimeter phase law) |
| `example_aisim_vibration_sweep.yaml` | Vibration sensitivity sweep (mirror-motion phase response) |

```bash
# Run all three
scripts/run_aisim_gravimeter_studies.sh
```

See [docs/AISIM_GRAVIMETER_STUDIES.md](docs/AISIM_GRAVIMETER_STUDIES.md) for the scientific meaning and limitations of each study.

---

## Repository layout

```
qgrav/
  configs/                      # YAML pipeline configurations
  data/raw/sg_sample/           # bundled sample station for testing
  docs/                         # detailed documentation
  scripts/                      # batch processing and utility scripts
  src/qgrav/
    algorithms/                 # signal processing algorithms
    bench_ifo/                  # interferometer bench (virtual, real, real_gravity)
    datasets/                   # data loaders (IGETS/GGP, CSV)
    metrics/                    # PSD, Allan deviation, noise ID, error stats
    physics/                    # phase models, sensitivity, systematics
    reporting/                  # HTML report generation (Jinja2)
    sim_ai/                     # AISim adapter layer
    validation/                 # published references, curve comparison
    gui/                        # tkinter desktop application
      widgets/                  # extracted MetricCards, ScrollableFrame
      app.py                    # main GUI application
    visuals.py                  # matplotlib figure builders
    pipeline.py                 # orchestrates the full run
    cli.py                      # CLI entry point
  tests/                        # 79 tests (pytest)
```

---

## Tests

```bash
# Set backend for headless matplotlib (avoids tkinter display issues)
# PowerShell:
$env:MPLBACKEND = "Agg"
# Bash:
export MPLBACKEND=Agg

# Run all tests
python -m pytest -q

# Verbose with tracebacks
python -m pytest -v --tb=short
```

**79 tests** covering: synthetic pipeline, AISim integration, GUI imports, visual generation, `.ggp` parsing, CSV conversion, real gravimetry pipeline, Allan deviation backends, noise identification, shot-noise sensitivity, systematics, published references, batch scripts, and float tau matching edge cases.

---

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Full change log with commit hashes |
| [GUIDE.md](GUIDE.md) | User guide and workflow documentation |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture overview |
| [docs/SCIENTIFIC_HARDENING.md](docs/SCIENTIFIC_HARDENING.md) | What is AISim-backed vs. hybrid vs. analytic |
| [docs/AISIM_INTEGRATION.md](docs/AISIM_INTEGRATION.md) | AISim vendor integration details |
| [docs/AISIM_GRAVIMETER_STUDIES.md](docs/AISIM_GRAVIMETER_STUDIES.md) | Scientific meaning of each AISim study |
| [docs/REAL_GRAVITY_DATA.md](docs/REAL_GRAVITY_DATA.md) | Real gravimetry data ingestion guide |
| [docs/GUI.md](docs/GUI.md) | Desktop GUI documentation |
| [docs/REPRODUCTION.md](docs/REPRODUCTION.md) | Reproducing pipeline runs |

---

## Dependencies

| Package | Version | Used by |
|---------|---------|---------|
| numpy | >= 1.23 | Core |
| matplotlib | >= 3.7 | Core |
| pyyaml | >= 6.0 | Core |
| jinja2 | >= 3.1 | Core (reporting) |
| scipy | >= 1.6 | Vendored allantools and vendor/aisim only |

---

## What's new in v0.7.0

Upgrade from v0.5.0 with **+1503 lines** across **33 files**, followed by a comprehensive code audit.

**Stabilization (Track A):** Dashboard rendering fix, semicolon reformatting, dropped-row tracking, float tau matching rewrite (230x speedup), GUI temp file cleanup, dependency documentation.

**Scientific validation (Track B):** Shot-noise sensitivity function, sensitivity in all AISim MZ outputs, noise type identification (5 types via log-log slope), Allan minimum finder, systematic effects module (gravity gradient + Coriolis), published references registry with DOIs.

**GUI & infrastructure (Track C):** GUI split into package with extracted widgets, IGETS unit format expansion, batch processing scripts, Allan noise annotations on all plots, systematics table in HTML reports.

**Code audit:** 8 bugs fixed (negative k_eff, Coriolis sign error, O(n^2) tau matching, format string crash, etc.) + 6 quality improvements (zero-value tolerance, DOI links, autoescape, logging, batch script tests).

See [CHANGELOG.md](CHANGELOG.md) for the full commit-by-commit breakdown.
