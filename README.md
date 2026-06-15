# qgrav - Software-first R&D pipeline for atom-interferometric gravimetry

[![Tests](https://github.com/adityagit94/Quantum-Gravitometer/actions/workflows/test.yml/badge.svg)](https://github.com/adityagit94/Quantum-Gravitometer/actions/workflows/test.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docs](https://img.shields.io/badge/docs-online-success.svg)](https://adityagit94.github.io/Quantum-Gravitometer/)

> **Highlights** - a gravity phase that **emerges** from a simulated ballistic
> trajectory under a chirped Raman laser (not injected analytically), now with
> **sub-pulse finite-τ Raman integration** that converges to the Bertoldi 2019
> closed form; **multi-drop measurement cycles** with a per-shot noise budget,
> **emergent Monte-Carlo quantum projection noise**, and a fringe-lock servo that
> yield ASD / Allan curves like a real instrument; **one-click reproductions** of
> five published transportable gravimeters; an independent **QuTiP** cross-check
> of the Raman dynamics (agreement ~1.6×10⁻⁶); real **IGETS**
> superconducting-gravimeter analysis with a complete tide → pressure → polar-motion
> → ocean-loading residual chain; and a six-tab desktop **GUI**.
> **450 tests, green on Python 3.11-3.13.**
> See [CHANGELOG.md](CHANGELOG.md) and [docs/ROADMAP_V1_TO_V2.md](docs/ROADMAP_V1_TO_V2.md).

**qgrav** is a software-first R&D pipeline for atom-interferometric gravimetry: simulation, real-data analysis, and reporting. It connects an atom-optics simulator (AISim) with **emergent gravity-phase physics**, a virtual interferometer, real gravity-residual ingest, statistical analysis (PSD, Allan deviation with multiple backends, noise-type identification), multi-drop measurement cycles, and an auto-generated HTML report - all driven from a single YAML config.

### What this is

- A reproducible pipeline that takes synthetic or real time-series in and writes a versioned run folder out (raw arrays, metrics JSON, plots, HTML report).
- A research workbench for designing and benchmarking atom-interferometer parameters against published instruments.
- **A self-consistent numerical gravimeter simulation**: gravity phase emerges from a ballistic atom trajectory under a chirped Raman laser, not from injecting `k_eff·g·T²` analytically. An optional hybrid mode keeps the analytical path available.
- An honest tool: every simulation result carries a **study-scope label** (fully simulated / hybrid / analytical only) so users can tell at a glance what is computed from first principles vs imposed analytically.

**Documentation:** the full user guide, physics design, and validation notes are published at **<https://adityagit94.github.io/Quantum-Gravitometer/>**. See [CHANGELOG.md](CHANGELOG.md) for the change history.

**Author:** Aditya Prakash | **License:** GPL-3.0 | **Python:** >= 3.11

---

## What it does

| Stage | Description |
|-------|-------------|
| **Simulate** | AISim-backed atom interferometry: Rabi scans, Mach-Zehnder phase scans, gravity sweeps, vibration sensitivity sweeps, **emergent-gravity simulations** (with sub-pulse finite-τ Raman integration), and **multi-drop measurement cycles** |
| **Generate** | Virtual interferometer I/Q data with known truth displacement for algorithm benchmarking, plus **NLNM/NHNM time-domain vibration noise** |
| **Ingest** | Real gravimetry time-series from `.ggp`, `.zip`, directory, or CSV (superconducting gravimeter residuals) |
| **Analyze** | PSD, overlapping Allan deviation (custom + AllanTools backends), noise type classification, shot-noise sensitivity, and **per-drop Allan deviation** |
| **Validate** | Published-reference comparison (Freier 2016, Ménoret 2018, and three more), systematic-effect estimation, backend cross-checks, and **AC-Stark light-shift and wavefront-aberration sensitivity** |
| **Report** | Auto-generated HTML reports with plots, metrics, systematics tables, and full config snapshots |
| **GUI** | tkinter desktop app (6 tabs): config editing, pipeline execution, interactive plots, multi-run Allan-curve comparison, a Validation tab with one-click published-paper reproductions and a QuTiP cross-check, and a navigable in-app guide |

---

## Validation & quality

qgrav is checked against the published literature and an independent solver, not only against itself:

- **Published-instrument regressions.** The automated suite reproduces the short-term sensitivity of five transportable atom gravimeters from their documented parameters and noise budgets - **Freier 2016 (GAIN)** as the primary target, plus **Hu 2013**, **Ménoret 2018**, **Xu 2022**, and **Wu 2019** - each within its documented tolerance band. One-click reproductions ship in the GUI's **Validation** tab.
- **Independent cross-validation.** The single-pulse Raman dynamics are reproduced by an independent **QuTiP** Schrödinger integration to ~1.6×10⁻⁶, and match the closed-form Rabi solution to ~1×10⁻¹⁵.
- **Real precision-gravity data.** The analysis chain is validated on bundled real **IGETS** superconducting-gravimeter data against the published instrument noise floor.
- **Emergent physics.** In fully-simulated mode the `k_eff·g·T²` gravity phase emerges from first principles (ballistic free-fall + chirped laser), confirmed against the analytical result and the **Bertoldi 2019** finite-pulse closed form (the sub-pulse integrator converges to within 2×10⁻³ relative).
- **Quantum projection noise.** In multi-drop mode the shot-noise floor emerges from `Binomial(N_det, P)` single-atom statistics and matches the analytic `σ_g = 1/(√N_det·k_eff·T²)` to 0.2 %.
- **450 automated tests**, green on Linux and Windows across Python 3.11-3.13.

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

This creates a timestamped folder under `runs/` - open `report.html` in your browser for the full results.

### More examples

```bash
# AISim Rabi scan
qgrav run --config configs/example_aisim.yaml

# AISim Mach-Zehnder phase scan
qgrav run --config configs/example_aisim_phase_scan.yaml

# AISim gravity sweep - hybrid mode (analytical gravity phase)
qgrav run --config configs/example_aisim_gravity_sweep.yaml

# AISim gravity sweep - fully simulated (gravity phase emerges from the simulation)
# Add `gravity_propagation: true` to the simulation block of any AISim config.

# AISim vibration sensitivity sweep
qgrav run --config configs/example_aisim_vibration_sweep.yaml

# AISim multi-drop measurement cycle (ASD / Allan deviation)
qgrav run --config configs/example_aisim_multi_drop.yaml

# Real gravimetry (requires data in data/raw/sg_sample/)
qgrav run --config configs/example_real_gravity.yaml
```

### Programmatic use - multi-drop measurement cycle

```python
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle

result = run_aisim_multi_drop_cycle(
    n_drops=100,             # 100 independent drops
    cycle_time_s=1.0,        # 1 Hz cycle rate
    gravity_true_m_s2=9.81,
    gravity_propagation=True,  # emergent-gravity mode
    raman_substeps=8,          # sub-pulse finite-τ Raman integration (v1.5)
    detection_noise_enabled=True,
    n_detected_per_drop=1000,
    projection_noise=True,     # emergent Monte-Carlo quantum projection noise (v1.5)
    servo_enabled=True,        # closed-loop fringe lock
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
- **Noise type identification** - via lag-1 autocorrelation (primary, ACF) or legacy log-log slope fit
- **Allan minimum** - optimal averaging time
- **Shot-noise sensitivity** - `1/(C * k_eff * T^2 * sqrt(N/T_cycle))` in m/s^2/sqrt(Hz) and uGal/sqrt(Hz)
- **Systematic effects** - gravity gradient shift, Coriolis shift (order-of-magnitude estimates)
- **Output format version** - `qgrav_output_format_version: "1.0"` for downstream consumers
- **Corrections metadata** - `data_product_level_at_analysis`, `corrections_applied`, `correction_metrics` (when corrections enabled)
- Gap report (for real gravity data)

---

## Scientific features

### Shot-noise sensitivity
Computes the quantum projection noise limit for atom interferometer gravimeters:

```
delta_g = 1 / (C * k_eff * T^2 * sqrt(N / T_cycle))
```

Available as `shot_noise_sensitivity_m_s2_per_sqrt_hz()` and `sensitivity_ugal_per_sqrt_hz()` in `qgrav.physics`. In the multi-drop cycle the floor can instead **emerge** from per-drop `Binomial(N_det, P)` draws (`projection_noise: true`).

### Noise type identification

Two complementary methods:

- **ACF method (primary, v0.8)** - lag-1 autocorrelation (Riley 2004) applied directly to the time series. More robust for mixed noise types. Uses `allantools.ci.autocorr_noise_id`.
- **Slope method (legacy)** - fits the log-log slope of the Allan deviation curve. Classifies into 5 standard noise types:

| Slope | Noise type |
|-------|-----------|
| -1.0 | White phase modulation |
| -0.75 | Flicker phase modulation |
| -0.5 | White frequency modulation |
| -0.25 | Flicker frequency modulation |
| +0.5 | Random walk frequency modulation |

Both methods are stored in `metrics.json`. The ACF result is under `noise_identification`; the slope result is under `noise_identification.legacy_slope_method`.

### Systematic effects
Order-of-magnitude analytical estimates of the leading systematic shifts:
- **Gravity gradient** - vertical free-air gradient effect during free fall
- **Coriolis** - Earth rotation coupling with horizontal atomic velocity

### Sensitivity function and vibration transfer function

The three-pulse Mach-Zehnder sensitivity function g_s(t) (Cheinet 2008) quantifies how laser-phase or mirror-vibration perturbations translate into interferometer phase shift. Available functions:

- `sensitivity_function_time_domain()` - time-domain g_s(t) for instantaneous or finite-duration pulses
- `transfer_function_vibration()` - |G(2πf)|² with notches at f = n/T and 1/f² rolloff
- `acceleration_to_phase_transfer_function_sq()` - |H_a(2πf)|² for acceleration PSD input
- `integrate_vibration_noise()` - broadband integrator returning equivalent gravity noise σ_g

Built-in Peterson 1993 NLNM/NHNM seismic noise models are available as reference acceleration PSDs for vibration-limited noise budgets.

### Real-gravimetry residual chain (tide, pressure, polar motion, ocean loading)

For IGETS Level 1 or Level 2 data, enable `apply_corrections: true` in `bench_real_gravity` to run the standard superconducting-gravimeter residual chain, in order:

1. **Solid-earth body tide** - PyGTide (if installed) or internal 20-constituent HW95 model (~50 nGal RMS truncation error)
2. **Atmospheric pressure loading** - linear admittance model (-3 nm/s²/hPa default, Crossley 1995)
3. **Polar motion (pole tide)** - from user-supplied IERS C04 pole coordinates and the IERS gravimetric δ factor *(off by default)*
4. **Ocean tidal loading** - from user-supplied Onsala-BLQ constituent amplitudes and phases, reusing the HW95 astronomical-argument machinery *(off by default)*

Each stage follows the `corrected = observed − effect` convention, is fully offline, and is recorded in `metrics.json` under `correction_metrics`. The pipeline auto-detects the IGETS data product level from the sample rate and applies the corrections before Allan/PSD computation, so Allan deviation comparisons against published SG noise floors become meaningful. See [docs/REAL_GRAVITY_DATA.md](docs/REAL_GRAVITY_DATA.md) for the full config block.

### Published references
Frozen registry of **14** benchmark values with DOI links, used directly by the automated validation suite:

| Key | Value | Source |
|-----|-------|--------|
| `freier_2016_short_term_noise` | 9.6e-8 m/s²/√Hz | Freier et al. (2016) |
| `freier_2016_accuracy` | 3.9e-8 m/s² | Freier et al. (2016) |
| `freier_2016_long_term_stability` | 5e-10 m/s² | Freier et al. (2016) |
| `hu_2013_short_term_noise` | 4.2e-8 m/s²/√Hz | Hu et al. (2013) |
| `menoret_2018_short_term_noise` | 7.5e-7 m/s²/√Hz | Ménoret et al. (2018) |
| `menoret_2018_long_term_stability` | 1e-8 m/s² | Ménoret et al. (2018) |
| `peters_2001_accuracy` | 3e-8 m/s² | Peters, Chung & Chu (2001) |
| `kasevich_chu_1991_first_demo` | 3e-6 (Δg/g at 1000 s) | Kasevich & Chu (1991) |
| `bidel_2018_marine` | 8e-6 m/s²/√Hz | Bidel et al. (2018) |
| `bidel_2018_marine_static_uncertainty` | 1.7e-6 m/s² | Bidel et al. (2018) |
| `nlnm_low_freq` | 4e-10 m/s²/√Hz | Peterson (1993) |
| `sg_noise_floor` | 1.8e-9 m/s²/√Hz | Van Camp et al. |
| `sg_detectability_nGal` | 1e-11 m/s² | Hinderer et al. (2007) |
| `mz_visibility` | 0.5 | idealised MZ value |

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
| `multi_drop_cycle` (**v1.0**) | N independent drops with detection noise, projection noise, servo, Allan deviation | FULLY_SIMULATED |

```bash
# Run the classic three studies (hybrid mode)
scripts/run_aisim_gravimeter_studies.sh
```

To enable fully-simulated mode, add `gravity_propagation: true` to the simulation block of any gravity_sweep or vibration_sensitivity_sweep YAML config. Add `raman_substeps: N` (N > 1) to integrate the finite-duration Raman pulses sub-pulse.

See [docs/AISIM_GRAVIMETER_STUDIES.md](docs/AISIM_GRAVIMETER_STUDIES.md) for the scientific meaning and scope of each study, and [docs/V1_PHYSICS_UPGRADE.md](docs/V1_PHYSICS_UPGRADE.md) for the emergent-physics design.

---

## Repository layout

```
qgrav/
  configs/                      # YAML pipeline configurations
  data/raw/sg_sample/           # bundled sample station for tests
  docs/                         # detailed documentation
  paper/                        # JOSS paper draft
  scripts/                      # batch processing and utility scripts
  src/qgrav/
    algorithms/                 # baseline + improved signal-processing algorithms
    bench_ifo/                  # interferometer bench (virtual, real, real_gravity)
    datasets/                   # IGETS/GGP + CSV loaders, tide/pressure/polar/ocean corrections
    metrics/                    # PSD, Allan deviation, noise ID (ACF + slope), summaries
    physics/                    # constants, phase models, sensitivity function,
                                # noise models, readout/servo models, systematics, sources
    pipeline/                   # run orchestration (interferometer, gravity, simulation, plots)
    reporting/                  # HTML report generation (Jinja2)
    sim_ai/                     # AISim adapter layer
      aisim_adapter.py          #   facade re-exporting the split adapter modules
      _adapter_core.py          #   shared cloud/pulse helpers
      _scans.py / _sweeps.py    #   Rabi, MZ, gravity & vibration sweeps
      _multi_drop.py            #   multi-drop cycle, projection noise, servo
      _config_run.py            #   YAML-driven study dispatch
      _aisim_overrides.py       #   integrated-phase propagator, chirped wavevectors, sub-pulse
    validation/                 # published references (14 entries), per-paper setups,
                                # QuTiP cross-check, truth checks, curve comparison
    vendor/aisim/               # vendored AISim atom-optics core
    vendor/allantools/          # vendored Allan-deviation statistics
    gui/                        # tkinter desktop application (6 tabs incl. Validation)
      widgets/                  # MetricCards, ScrollableFrame, Tooltip, CollapsibleSection
      _tab_*.py                 # per-tab mixins (setup/run, data browser, editor, results, ...)
      app.py                    # main GUI application (assembles the tab mixins)
    config.py                   # YAML loading + validation
    visuals.py                  # matplotlib figure builders
    cli.py                      # CLI entry point (run, gui, convert-ggp, validate-data)
  tests/                        # 450 tests (pytest)
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

**450 tests** run green on Linux and Windows (Python 3.11-3.13). The v1.0 physics upgrade contributed 61 of them:

- Gravity-free ballistic propagator (10)
- Chirped-laser detuning (5)
- Gravity-enabled MZ + cross-validation (9)
- Time-domain vibration with NLNM/NHNM PSD (7)
- Detection noise & spontaneous emission (6)
- Multi-drop cycle, Allan deviation, study scope (10)
- Fringe-locking servo (6)
- AC Stark / light shift (3)
- Wavefront aberrations (5)

The v1.5 release added sub-pulse Raman integration, emergent projection noise, and the polar-motion / ocean-loading corrections, each with its own test module.

---

## Documentation

| Document | Description |
|----------|-------------|
| **[Online documentation](https://adityagit94.github.io/Quantum-Gravitometer/)** | The full rendered documentation site (recommended). |
| [docs/COMPLETE_GUIDE.md](docs/COMPLETE_GUIDE.md) | The complete user guide: install, run, configure, interpret results. |
| [CHANGELOG.md](CHANGELOG.md) | Full change log. |
| [GUIDE.md](GUIDE.md) | Quick-start workflow guide. |
| [docs/V1_PHYSICS_UPGRADE.md](docs/V1_PHYSICS_UPGRADE.md) | Emergent-physics design and equations. |
| [docs/PHYSICS_REVIEW_PACKET.md](docs/PHYSICS_REVIEW_PACKET.md) | **Comprehensive review packet for external atom-interferometry experts** (with executable notebook `docs/reviewer_notebook.ipynb`) |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture overview |
| [docs/SCIENTIFIC_HARDENING.md](docs/SCIENTIFIC_HARDENING.md) | What is AISim-backed vs. hybrid vs. analytic |
| [docs/AISIM_INTEGRATION.md](docs/AISIM_INTEGRATION.md) | AISim vendor integration details |
| [docs/AISIM_GRAVIMETER_STUDIES.md](docs/AISIM_GRAVIMETER_STUDIES.md) | Scientific meaning of each AISim study |
| [docs/REAL_GRAVITY_DATA.md](docs/REAL_GRAVITY_DATA.md) | Real gravimetry data ingestion and corrections guide |
| [docs/GUI.md](docs/GUI.md) | Desktop GUI documentation |
| [docs/REPRODUCTION.md](docs/REPRODUCTION.md) | Reproducing pipeline runs |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, tests, code style, PR flow |
| [SECURITY.md](SECURITY.md) · [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) | Security policy · community standards |

---

## Contributing & citing

Contributions are welcome - see [CONTRIBUTING.md](CONTRIBUTING.md) for dev setup,
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
| qutip | >= 4.7 | Optional (`pip install qgrav[qutip]`) - independent cross-check |

---

## What's new

The current line (**v1.5.x**) centres on **emergent pulse physics and a complete residual chain** (v1.5.1 is a docs/packaging patch over v1.5.0):

- **Sub-pulse Raman integration** (`raman_substeps`) - finite-τ pulses are integrated as composed slices with ballistic fall during the pulse, converging to the Bertoldi 2019 / Fang 2018 closed form.
- **Emergent Monte-Carlo quantum projection noise** (`projection_noise`) - the shot-noise floor emerges from per-drop `Binomial(N_det, P)` statistics, matching the analytic limit to 0.2 %.
- **Polar-motion and ocean-loading reductions** complete the standard SG residual chain (tide → pressure → polar motion → ocean loading), both off by default and fully offline.
- **Multi-run Allan-curve comparison** in the GUI Results tab, overlaying σ(τ) from any number of run folders.
- **450 tests**, green on Python 3.11-3.13.

Earlier releases added multi-drop measurement cycles with a fringe-lock servo, one-click reproductions of five published transportable gravimeters, an independent **QuTiP** cross-check, real **IGETS** superconducting-gravimeter analysis, and the six-tab desktop **GUI**.

See **[CHANGELOG.md](CHANGELOG.md)** for the complete, version-by-version history.
