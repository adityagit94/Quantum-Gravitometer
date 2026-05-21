# qgrav v0.8.0 — Software-first R&D pipeline for atom-interferometric gravimetry

**qgrav** is a software-first R&D pipeline for atom-interferometric gravimetry: simulation, real-data analysis, and reporting. It connects an atom-optics simulator (AISim), a virtual interferometer, real gravity-residual ingest, statistical analysis (PSD, Allan deviation with multiple backends, noise-type identification), and an auto-generated HTML report — all driven from a single YAML config.

### What this is

- A reproducible pipeline that takes synthetic or real time-series in and writes a versioned run folder out (raw arrays, metrics JSON, plots, HTML report).
- A research workbench for designing and benchmarking atom-interferometer parameters against published instruments.
- An honest tool: every simulation result carries a **study-scope label** (fully simulated / hybrid / analytical only) so users can tell at a glance what is computed from first principles vs imposed analytically.

### What this is not

- Hardware control: there is no GPIB / serial / real-time loop.
- A general-purpose geodynamics suite: the v0.8 tide / pressure correction stage exists only to make IGETS Allan-deviation comparisons meaningful. For serious geodynamics use PyGTide, ETERNA, or SPOTL.
- A competitor to dedicated research-group simulation codes (Mueller/Berkeley, SYRTE, Stanford, Humboldt). The AISim integration is the simulation core; qgrav wraps and extends it.

See `docs/COMPLETE_GUIDE.md` for the full user guide and `CHANGELOG.md` for the v0.7 → v0.8 changes.

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
- **Noise type identification** — via lag-1 autocorrelation (primary, ACF) or legacy log-log slope fit
- **Allan minimum** — optimal averaging time
- **Shot-noise sensitivity** — `1/(C * k_eff * T^2 * sqrt(N/T_cycle))` in m/s^2/sqrt(Hz) and uGal/sqrt(Hz)
- **Systematic effects** — gravity gradient shift, Coriolis shift (order-of-magnitude estimates)
- **Output format version** — `qgrav_output_format_version: "1.0"` for downstream consumers
- **Corrections metadata** — `data_product_level_at_analysis`, `corrections_applied`, `correction_metrics` (when corrections enabled)
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

Two complementary methods:

- **ACF method (primary, v0.8)** — lag-1 autocorrelation (Riley 2004) applied directly to the time series. More robust for mixed noise types. Uses `allantools.ci.autocorr_noise_id`.
- **Slope method (legacy)** — fits the log-log slope of the Allan deviation curve. Classifies into 5 standard noise types:

| Slope | Noise type |
|-------|-----------|
| -1.0 | White phase modulation |
| -0.75 | Flicker phase modulation |
| -0.5 | White frequency modulation |
| -0.25 | Flicker frequency modulation |
| +0.5 | Random walk frequency modulation |

Both methods are stored in `metrics.json`. The ACF result is under `noise_identification`; the slope result is under `noise_identification.legacy_slope_method`.

### Systematic effects
Order-of-magnitude estimates (clearly documented as **not** included in AISim simulation):
- **Gravity gradient** — vertical free-air gradient effect during free fall
- **Coriolis** — Earth rotation coupling with horizontal atomic velocity

### Sensitivity function and vibration transfer function

The three-pulse Mach-Zehnder sensitivity function g_s(t) (Cheinet 2008) quantifies how laser-phase or mirror-vibration perturbations translate into interferometer phase shift. Available functions:

- `sensitivity_function_time_domain()` — time-domain g_s(t) for instantaneous or finite-duration pulses
- `transfer_function_vibration()` — |G(2πf)|² with notches at f = n/T and 1/f² rolloff
- `acceleration_to_phase_transfer_function_sq()` — |H_a(2πf)|² for acceleration PSD input
- `integrate_vibration_noise()` — broadband integrator returning equivalent gravity noise σ_g

Built-in Peterson 1993 NLNM/NHNM seismic noise models are available as reference acceleration PSDs for vibration-limited noise budgets.

### Tide and pressure corrections (real gravimetry)

For IGETS Level 1 or Level 2 data, enable `apply_corrections: true` in `bench_real_gravity` to subtract:

1. **Solid-earth body tide** — PyGTide (if installed) or internal 20-constituent HW95 model (~50 nGal RMS truncation error)
2. **Atmospheric pressure loading** — linear admittance model (-3 nm/s²/hPa default, Crossley 1995)

The pipeline auto-detects the IGETS data product level from sample rate, applies corrections before Allan/PSD computation, and records what was applied in `metrics.json`. This makes Allan deviation comparisons against published SG noise floors meaningful for un-corrected input data.

### Published references
Frozen registry of 12 benchmark values with DOI links for validation:

| Key | Value | Source |
|-----|-------|--------|
| `freier_2016_short_term_noise` | 9.6e-8 m/s²/√Hz | Freier et al. (2016) |
| `freier_2016_accuracy` | 3.9e-8 m/s² | Freier et al. (2016) |
| `freier_2016_long_term_stability` | 5e-10 m/s² | Freier et al. (2016) |
| `menoret_2018_short_term_noise` | 5e-7 m/s²/√Hz | Menoret et al. (2018) |
| `menoret_2018_long_term_stability` | 1e-8 m/s² | Menoret et al. (2018) |
| `hu_2013_short_term_noise` | 4.2e-9 m/s²/√Hz | Hu et al. (2013) |
| `peters_2001_accuracy` | 3e-8 m/s² | Peters, Chung & Chu (2001) |
| `kasevich_chu_1991_first_demo` | 3e-6 m/s²/√Hz | Kasevich & Chu (1991) |
| `bidel_2018_marine` | 1.7e-6 m/s²/√Hz | Bidel et al. (2018) |
| `nlnm_low_freq` | 7e-10 m/s²/√Hz | Peterson (1993) |
| `sg_noise_floor` | 1e-11 m/s²/√Hz | Hinderer et al. (2007) |
| `mz_visibility` | 0.5 | Peters et al. (2001) |

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
      corrections.py            #   tide + pressure corrections (v0.8)
      _tides_hw95.py            #   20-constituent HW95 internal tide model
    metrics/                    # PSD, Allan deviation, noise ID (ACF + slope), error stats
    physics/                    # phase models, sensitivity, systematics
      constants.py              #   physical constants registry (v0.8)
      sensitivity_function.py   #   MZ sensitivity function + vibration integrator (v0.8)
      _seismic_models.py        #   Peterson NLNM/NHNM noise floor models (v0.8)
    reporting/                  # HTML report generation (Jinja2)
    sim_ai/                     # AISim adapter layer (study_scope labels)
    validation/                 # published references (12 entries), curve comparison
    gui/                        # tkinter desktop application
      widgets/                  # extracted MetricCards, ScrollableFrame
      app.py                    # main GUI application
    config.py                   # YAML loading, validation (incl. corrections keys)
    visuals.py                  # matplotlib figure builders
    pipeline.py                 # orchestrates the full run (corrections stage, output_format_version)
    cli.py                      # CLI entry point
  tests/                        # 134 tests (pytest)
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

**134 tests** covering: synthetic pipeline, AISim integration, GUI imports, visual generation, `.ggp` parsing, CSV conversion, real gravimetry pipeline, Allan deviation backends, noise identification (ACF + slope), shot-noise sensitivity, systematics, published references (12 entries + deprecation shims), physical constants regression, sensitivity function (time-domain + frequency-domain + integrator), tide/pressure corrections, unit conversions, study-scope labels, batch scripts, and float tau matching edge cases.

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

## What's new in v0.8.0

Milestone 1 of the Physics PRD: scientific foundations. **55 new tests** (79 → 134 passing).

**Physical constants (W1):** All hardcoded numerical literals (wavelengths, masses, Earth rotation rate, free-air gradient, gravity defaults) replaced with a frozen `PhysicalConstant` registry in `physics/constants.py`. Published references expanded from 4 to 12 entries with deprecation shims for renamed keys.

**Sensitivity function (W2):** Mach-Zehnder time-domain sensitivity function g_s(t), laser-phase transfer function |G(2πf)|², acceleration-to-phase transfer function |H_a(2πf)|², and broadband vibration noise integrator. Peterson 1993 NLNM/NHNM seismic noise models bundled for vibration-limited noise budgets.

**Corrections (W6):** Solid-earth tide correction (PyGTide or internal 20-constituent HW95 fallback) and atmospheric pressure correction (linear admittance). IGETS data product level auto-detection. Gated on `apply_corrections: true` for backwards compatibility.

**ACF noise ID (W9):** Lag-1 autocorrelation noise identification (Riley 2004) as primary method, with legacy slope-fit preserved as cross-check.

**Study scope labels (W10):** Every AISim simulation carries a `study_scope_category` (FULLY_SIMULATED / HYBRID / ANALYTICAL_ONLY) with colour-coded panels in the HTML report.

**Pipeline:** `qgrav_output_format_version: "1.0"` in every `metrics.json`. Corrections stage runs between data load and Allan/PSD for real gravimetry. Level-banner warning when IGETS Level < 3.

See [CHANGELOG.md](CHANGELOG.md) for the full breakdown.
