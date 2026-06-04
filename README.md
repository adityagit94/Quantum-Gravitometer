# qgrav v1.3.0 — Software-first R&D pipeline for atom-interferometric gravimetry

[![Tests](https://github.com/adityagit94/Quantum-Gravitometer/actions/workflows/test.yml/badge.svg)](https://github.com/adityagit94/Quantum-Gravitometer/actions/workflows/test.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

> **v1.2–v1.3 hardening highlights** (on top of the v1.1 published-reference
> release): an independent **QuTiP** cross-validation backend (reproduces the
> Raman dynamics to ~1.6×10⁻⁶); the finite-ensemble-floor finding that let the
> Freier regression tighten to **factor 2** and the secondary benchmarks to
> factor 3; the **Bertoldi 2019** closed-form finite-τ predictor; quantitative
> **wavefront-curvature** validation; full gravity-sweep **YAML exposure** of
> AC-Stark + wavefront; a **performance** harness (single MZ ~1.3 ms); **real
> IGETS superconducting-gravimeter** analysis-chain validation; a **JOSS paper**
> draft and a **MkDocs** site; and an honest **scientific-package evaluation**
> (QuTiP integrated; Qiskit/GEANT4/LAMMPS documented as not applicable).
> **378 tests pass.** See [CHANGELOG.md](CHANGELOG.md) and
> [docs/ROADMAP_V1_TO_V2.md](docs/ROADMAP_V1_TO_V2.md).



**qgrav** is a software-first R&D pipeline for atom-interferometric gravimetry: simulation, real-data analysis, and reporting. It connects an atom-optics simulator (AISim) with **emergent gravity-phase physics**, a virtual interferometer, real gravity-residual ingest, statistical analysis (PSD, Allan deviation with multiple backends, noise-type identification), multi-drop measurement cycles, and an auto-generated HTML report — all driven from a single YAML config.

### What this is

- A reproducible pipeline that takes synthetic or real time-series in and writes a versioned run folder out (raw arrays, metrics JSON, plots, HTML report).
- A research workbench for designing and benchmarking atom-interferometer parameters against published instruments.
- **A self-consistent numerical gravimeter simulation (v1.0+)**: gravity phase emerges from a ballistic atom trajectory under a chirped Raman laser, not from injecting `k_eff·g·T²` analytically. Optional fall-back to the hybrid mode for backward compatibility.
- An honest tool: every simulation result carries a **study-scope label** (fully simulated / hybrid / analytical only) so users can tell at a glance what is computed from first principles vs imposed analytically.

### What this is not

- Hardware control: there is no GPIB / serial / real-time loop.
- A general-purpose geodynamics suite: the v0.8 tide / pressure correction stage exists only to make IGETS Allan-deviation comparisons meaningful. For serious geodynamics use PyGTide, ETERNA, or SPOTL.
- A competitor to dedicated research-group simulation codes (Mueller/Berkeley, SYRTE, Stanford, Humboldt). The AISim integration is the simulation core; qgrav wraps and extends it.

See `docs/COMPLETE_GUIDE.md` for the full user guide, `docs/V1_PHYSICS_UPGRADE.md` for the v1.0 emergent-physics design, and `CHANGELOG.md` for the v0.9 → v1.0 changes.

**Author:** Aditya Prakash | **License:** GPL-3.0 | **Python:** >= 3.10

---

## What it does

| Stage | Description |
|-------|-------------|
| **Simulate** | AISim-backed atom interferometry: Rabi scans, Mach-Zehnder phase scans, gravity sweeps, vibration sensitivity sweeps, **emergent-gravity simulations (v1.0)**, **multi-drop measurement cycles (v1.0)** |
| **Generate** | Virtual interferometer I/Q data with known truth displacement for algorithm benchmarking, **NLNM/NHNM time-domain vibration noise (v1.0)** |
| **Ingest** | Real gravimetry time-series from `.ggp`, `.zip`, directory, or CSV (superconducting gravimeter residuals) |
| **Analyze** | PSD, overlapping Allan deviation (custom + AllanTools backends), noise type classification, shot-noise sensitivity, **per-drop Allan deviation (v1.0)** |
| **Validate** | Published reference comparison (Freier 2016, Menoret 2018, etc.), systematic effects estimation, backend cross-checks, **AC Stark light-shift and wavefront-aberration sensitivity (v1.0)** |
| **Report** | Auto-generated HTML reports with plots, metrics, systematics tables, and full config snapshots |
| **GUI** | tkinter desktop app (6 tabs): config editing, pipeline execution, interactive plots, a Validation tab with one-click published-paper reproductions and a QuTiP cross-check, and a navigable in-app guide |

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

# AISim gravity sweep — hybrid mode (analytical gravity phase)
qgrav run --config configs/example_aisim_gravity_sweep.yaml

# AISim gravity sweep — fully simulated (v1.0: gravity phase EMERGES from simulation)
# Add `gravity_propagation: true` to the simulation block of any AISim config.

# AISim vibration sensitivity sweep
qgrav run --config configs/example_aisim_vibration_sweep.yaml

# Real gravimetry (requires data in data/raw/sg_sample/)
qgrav run --config configs/example_real_gravity.yaml
```

### Programmatic use — multi-drop measurement cycle (v1.0)

```python
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle

result = run_aisim_multi_drop_cycle(
    n_drops=100,             # 100 independent drops
    cycle_time_s=1.0,        # 1 Hz cycle rate
    gravity_true_m_s2=9.81,
    gravity_propagation=True,  # emergent-gravity mode
    detection_noise_enabled=True,
    n_detected_per_drop=1000,
    servo_enabled=True,       # closed-loop fringe lock
    servo_gain=0.5,
)

print(f"Mean g = {result['mean_g_m_s2']:.9f} m/s^2")
print(f"Allan deviation at tau=1s: {result['allan_dev_m_s2'][0]:.2e}")
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

Five thesis/report-quality simulation studies:

| Model | Study | Scope |
|-------|-------|-------|
| `rabi_scan` | Rabi-oscillation π/2 calibration | FULLY_SIMULATED |
| `mach_zehnder_phase_scan` | Three-pulse MZ fringe | FULLY_SIMULATED |
| `gravity_sweep` (default) | Hybrid gravity response (AISim pulse + analytical k_eff g T²) | HYBRID |
| `gravity_sweep` + `gravity_propagation: true` (**v1.0**) | Emergent gravity from ballistic trajectory + chirped laser | FULLY_SIMULATED |
| `vibration_sensitivity_sweep` | Mirror-motion vibration response | HYBRID / FULLY_SIMULATED |
| `multi_drop_cycle` (**v1.0**) | N independent drops with detection noise, servo, Allan deviation | FULLY_SIMULATED |

```bash
# Run the classic three studies (hybrid mode)
scripts/run_aisim_gravimeter_studies.sh
```

To enable fully-simulated mode, add `gravity_propagation: true` to the simulation block of any gravity_sweep or vibration_sensitivity_sweep YAML config.

See [docs/AISIM_GRAVIMETER_STUDIES.md](docs/AISIM_GRAVIMETER_STUDIES.md) for the scientific meaning and limitations of each study, and [docs/V1_PHYSICS_UPGRADE.md](docs/V1_PHYSICS_UPGRADE.md) for the v1.0 emergent-physics design.

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
    sim_ai/                     # AISim adapter layer
      aisim_adapter.py          #   gravity sweep, vibration sweep, multi-drop cycle,
                                #   calibration (v1.0), wavefront wiring (v1.0)
    validation/                 # published references (12 entries), curve comparison
                                # truth_checks expanded to handle simulated-gravity
                                # and multi_drop_cycle (v1.0)
    vendor/aisim/               # patched AISim core (v1.0)
      prop.py                   #   GravityFreePropagator (v1.0), integrated-phase patch,
                                #   AC Stark correction (v1.0)
      beam.py                   #   Wavevectors with chirp_rate (v1.0)
    gui/                        # tkinter desktop application (6 tabs incl. Validation)
      widgets/                  # MetricCards, ScrollableFrame, Tooltip, CollapsibleSection
      app.py                    # main GUI application
    config.py                   # YAML loading, validation (incl. corrections keys)
    visuals.py                  # matplotlib figure builders
    pipeline.py                 # orchestrates the full run (corrections stage, output_format_version)
    cli.py                      # CLI entry point
  tests/                        # 253 tests (pytest) - up from 192 baseline
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

**253 tests** covering everything in v0.9 (192) plus **61 new v1.0 tests**:

- Gravity-free ballistic propagator (10)
- Chirped-laser detuning (5)
- Gravity-enabled MZ + cross-validation (9)
- Time-domain vibration with NLNM/NHNM PSD (7)
- Detection noise & spontaneous emission (6)
- Multi-drop cycle, Allan deviation, study scope (10)
- Fringe-locking servo (6)
- AC Stark / light shift (3)
- Wavefront aberrations (5)

---

## Documentation

| Document | Description |
|----------|-------------|
| [CHANGELOG.md](CHANGELOG.md) | Full change log with commit hashes |
| [GUIDE.md](GUIDE.md) | User guide and workflow documentation |
| [docs/V1_PHYSICS_UPGRADE.md](docs/V1_PHYSICS_UPGRADE.md) | **v1.0 emergent-physics design (start here for v1.0)** |
| [docs/PHYSICS_REVIEW_PACKET.md](docs/PHYSICS_REVIEW_PACKET.md) | **Comprehensive review packet for external atom-interferometry experts** (with executable notebook `docs/reviewer_notebook.ipynb`) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture overview |
| [docs/SCIENTIFIC_HARDENING.md](docs/SCIENTIFIC_HARDENING.md) | What is AISim-backed vs. hybrid vs. analytic |
| [docs/AISIM_INTEGRATION.md](docs/AISIM_INTEGRATION.md) | AISim vendor integration details |
| [docs/AISIM_GRAVIMETER_STUDIES.md](docs/AISIM_GRAVIMETER_STUDIES.md) | Scientific meaning of each AISim study |
| [docs/REAL_GRAVITY_DATA.md](docs/REAL_GRAVITY_DATA.md) | Real gravimetry data ingestion guide |
| [docs/GUI.md](docs/GUI.md) | Desktop GUI documentation |
| [docs/REPRODUCTION.md](docs/REPRODUCTION.md) | Reproducing pipeline runs |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, tests, code style, PR flow |
| [SECURITY.md](SECURITY.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Security policy · community standards |

---

## Contributing & citing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup,
the test commands, and the project's guiding principles, and
[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Report bugs and request features via the
GitHub issue templates; report vulnerabilities privately per [SECURITY.md](SECURITY.md).

If you use qgrav in academic work, please cite it via the **"Cite this
repository"** button on GitHub (backed by [CITATION.cff](CITATION.cff)).

qgrav vendors [AISim](https://github.com/bleykauf/aisim) (GPL-3.0) and
[allantools](https://github.com/aewallin/allantools) (LGPL-3.0); see
[`src/qgrav/vendor/ATTRIBUTION.md`](src/qgrav/vendor/ATTRIBUTION.md).

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

## What's new in v1.0.0

**Full physics simulation upgrade.** Transforms qgrav from a hybrid analytical+AISim wrapper into a self-consistent numerical gravimeter simulation. **61 new tests** (192 → 253 passing). All previous tests pass unchanged.

### Tier 1 — Emergent gravity physics

- **`GravityFreePropagator`** (`vendor/aisim/prop.py`): exact ballistic kinematics under uniform gravity with optional linear gradient γ·(z − z_ref).
- **Chirped laser** (`vendor/aisim/beam.py`): `Wavevectors` accepts `chirp_rate_rad_per_s2`, cancelling gravity-induced Doppler at α = −k_eff · g_chirp.
- **Integrated-phase patch** (`vendor/aisim/prop.py`): replaces AISim's `exp(−i·δ·t₀)` with the physically correct `exp(−i·(−k_eff·z(t₀) + ½·chirp·t₀²))`. The MZ combination now produces the standard `k_eff·(g − g_chirp)·T²` gravity phase from first principles.
- **Per-sweep calibration** (`_calibrate_gravity_phase_offset`): removes residual pulse-timing offsets so simulated and hybrid modes share the same fringe centre at `g = g_chirp`.
- **`gravity_propagation: true`** in any `gravity_sweep` or `vibration_sensitivity_sweep` config promotes the run to `FULLY_SIMULATED`.

### Tier 2 — Realistic noise sources

- **Time-domain vibration generator** (`physics/noise_models.generate_vibration_timeseries`): Peterson NLNM/NHNM acceleration PSD + second-order isolation filter `H²(f) = f⁴/(f² + f_c²)²`. Returns acceleration, velocity and displacement time-series.
- **Detection (shot) noise** (`physics/noise_models.add_detection_noise`): σ = 1/√N_detected per population fraction.
- **Spontaneous emission probability** (`physics/noise_models.spontaneous_emission_loss_probability`): p_se = (Ω_eff/Δ)² · τ/τ_sp.

### Tier 3 — Multi-drop measurement cycle

- **`run_aisim_multi_drop_cycle`** (`sim_ai/aisim_adapter.py`): N independent drops, fresh ensemble per drop (seed + i), optional detection noise, optional integrator servo, overlapping Allan deviation.
- **`servo_integrator_step`** (`physics/readout_models.py`): one-step digital integrator that drives P3 toward the mid-fringe setpoint.

### Tier 4 — Advanced systematics

- **AC Stark / light shift** (`vendor/aisim/prop.py`): `single_photon_detuning_hz` adds Ω_eff²/(4Δ) to the two-photon detuning, with position-dependence from Ω_eff(r).
- **Wavefront aberrations** (`sim_ai/aisim_adapter._build_wavefront`): Zernike-polynomial wavefront wired into all three pulse propagators of the MZ sequence.

### Phase 10 — Truth checks & versioning

- `_check_gravity_sweep` now branches on `gravity_propagation`: hybrid runs check the analytical phase exactly; simulated runs check visibility > 0.3 and FULLY_SIMULATED scope.
- New `_check_multi_drop_cycle` validates n_drops correctness, finite estimates, monotonic timestamps, |mean(g) − g_true| < 1e-5, and Allan-array consistency.

See [CHANGELOG.md](CHANGELOG.md) for the full breakdown and [docs/V1_PHYSICS_UPGRADE.md](docs/V1_PHYSICS_UPGRADE.md) for the design rationale and equations.

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
