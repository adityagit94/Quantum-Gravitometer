# qgrav - Software-first R&D pipeline for atom-interferometric gravimetry

[![PyPI](https://img.shields.io/pypi/v/qgrav.svg)](https://pypi.org/project/qgrav/)
[![Tests](https://github.com/adityagit94/Quantum-Gravitometer/actions/workflows/test.yml/badge.svg)](https://github.com/adityagit94/Quantum-Gravitometer/actions/workflows/test.yml)
[![Python](https://img.shields.io/pypi/pyversions/qgrav.svg)](https://pypi.org/project/qgrav/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docs](https://img.shields.io/badge/docs-online-success.svg)](https://adityagit94.github.io/Quantum-Gravitometer/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20618573.svg)](https://doi.org/10.5281/zenodo.20618573)

**qgrav** is a complete quantum-gravimeter laboratory in software: it simulates
a Mach-Zehnder atom-interferometer gravimeter from first principles, runs
realistic multi-drop measurement campaigns, ingests real precision-gravity
data, and writes every result into a reproducible, self-documenting run
folder — all driven from a single YAML config, on a laptop, with no hardware.

**Author:** Aditya Prakash | **License:** GPL-3.0 | **Python:** ≥ 3.11 |
**Docs:** <https://adityagit94.github.io/Quantum-Gravitometer/>

---

## Why qgrav

- **Emergent physics, not injected formulas.** The gravity phase `k_eff·g·T²`
  emerges from a simulated ballistic trajectory under a chirped Raman laser -
  it is never inserted analytically (an optional hybrid mode keeps the
  analytical path available). Finite-duration pulses are integrated sub-pulse
  and converge to the Bertoldi 2019 closed form; the quantum projection-noise
  floor emerges from `Binomial(N_det, P)` single-atom statistics; the gravity
  gradient emerges from the trajectory and reproduces the Peters/Chung/Chu
  `(7/12)·γ·g·T⁴` closed form.
- **A real measurement campaign in software.** Multi-drop cycles with a
  per-shot noise budget - detection noise, Raman phase noise, and seismic
  vibration sampled from one continuous Peterson NLNM/NHNM series so drops
  are correlated through the common ground motion - plus a fringe-lock servo
  (integrator or anti-windup PID), producing ASD and Allan-deviation curves
  like a real instrument.
- **Validated against the literature, not against itself.** Automated
  regressions reproduce the short-term sensitivity of five published
  transportable gravimeters (Freier 2016 GAIN as the primary target, plus
  Hu 2013, Ménoret 2018, Xu 2022, Wu 2019); an independent QuTiP Schrödinger
  integration reproduces the Raman dynamics to ~1.6×10⁻⁶; the analysis chain
  is validated on bundled real IGETS superconducting-gravimeter data.
- **Honest by construction.** Every simulation result carries a study-scope
  label (fully simulated / hybrid / analytical only) rendered as a color-coded
  panel in the report, self-checking truth checks attached at run time, and a
  DOI-linked published-reference registry that keeps an in-code ledger of its
  own historical value bugs.
- **Reproducible by architecture.** One YAML in → one immutable timestamped
  run folder out: exact config snapshot, raw arrays (`data.npz`), metrics
  JSON, plots, and a self-contained HTML report. Seeded RNG streams govern
  every stochastic component.
- **Complete tooling.** A five-command CLI, a six-tab desktop GUI with
  one-click published-paper reproductions, a documentation site, a headless
  Docker image, and **490 automated tests** green on Linux and Windows across
  Python 3.11-3.13.

---

## Quick start

### Install

```bash
pip install qgrav
```

That pulls the latest release from [PyPI](https://pypi.org/project/qgrav/).
Optional extras: `pip install qgrav[qutip]` enables the independent QuTiP
cross-check backend. The desktop GUI also needs Tk - bundled with the
python.org installers; on Debian/Ubuntu run `sudo apt install python3-tk`.

**From source** (for development or the latest unreleased code):

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

This creates a timestamped folder under `runs/` - open `report.html` in your
browser for the full results.

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

# AISim vibration sensitivity sweep (add `vibration_model: time_domain` for
# Peterson-series mirror motion with an end-to-end Cheinet budget check)
qgrav run --config configs/example_aisim_vibration_sweep.yaml

# AISim multi-drop measurement cycle (ASD / Allan deviation)
qgrav run --config configs/example_aisim_multi_drop.yaml

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

## What it does

| Stage | Description |
|-------|-------------|
| **Simulate** | AISim-backed atom interferometry: Rabi scans, Mach-Zehnder phase scans, gravity sweeps (with emergent gravity and gravity-gradient physics), vibration sweeps (sinusoidal or time-domain Peterson mirror motion), and multi-drop measurement cycles with sub-pulse finite-τ Raman integration |
| **Generate** | Virtual interferometer I/Q data with known truth displacement for algorithm benchmarking, plus NLNM/NHNM time-domain vibration noise |
| **Ingest** | Real gravimetry time-series from `.ggp`, `.zip`, directory, or CSV (superconducting gravimeter residuals) |
| **Analyze** | PSD, overlapping Allan deviation (custom + AllanTools backends), noise-type classification, shot-noise sensitivity, and per-drop Allan deviation |
| **Validate** | Published-reference comparison (Freier 2016 and four more), closed-form truth checks on every result, QuTiP cross-check, AC-Stark and wavefront-aberration sensitivity |
| **Report** | Auto-generated HTML reports with plots, metrics, systematics tables, study-scope panels, and full config snapshots (credential-like values masked) |
| **GUI** | tkinter desktop app (6 tabs): config editing, pipeline execution, interactive plots, multi-run Allan-curve comparison, one-click published-paper reproductions, in-app guides |

---

## Validation & quality

qgrav is checked against the published literature and independent solvers, not
only against itself:

- **Published-instrument regressions.** The automated suite reproduces the
  short-term sensitivity of five transportable atom gravimeters from their
  documented parameters and noise budgets - **Freier 2016 (GAIN)** as the
  primary target, plus **Hu 2013**, **Ménoret 2018**, **Xu 2022**, and
  **Wu 2019** - each within its documented tolerance band. One-click
  reproductions ship in the GUI's **Validation** tab.
- **Independent cross-validation.** The single-pulse Raman dynamics are
  reproduced by an independent **QuTiP** Schrödinger integration to
  ~1.6×10⁻⁶, and match the closed-form Rabi solution to ~1×10⁻¹⁵.
- **Emergent physics vs closed forms.** The `k_eff·g·T²` gravity phase
  emerges from first principles and is confirmed against the analytical
  result; the sub-pulse integrator converges to the **Bertoldi 2019**
  finite-pulse closed form within 2×10⁻³; the emergent gravity-gradient
  phase matches the **Peters/Chung/Chu 2001** `(7/12)·γ·g·T⁴` closed form
  to ~0.1 %; the multi-drop shot-noise floor matches the analytic
  `σ_g = 1/(√N_det·k_eff·T²)` to 0.2 %.
- **Transfer function proven end-to-end.** In the time-domain vibration mode
  the realized per-shot phase noise reproduces the frequency-domain Cheinet
  budget `∫S_a·|H_a|²df` computed on the same PSD - checked automatically on
  every run.
- **Real precision-gravity data.** The analysis chain is validated on bundled
  real **IGETS** superconducting-gravimeter data against the published
  instrument noise floor.
- **490 automated tests** (fast suite in CI on Linux + Windows, Python
  3.11-3.13, with a coverage ratchet; slow published-reference regressions
  and benchmarks nightly).

---

## Simulation studies

| Model | Study | Scope |
|-------|-------|-------|
| `rabi_scan` | Rabi-oscillation π/2 calibration | FULLY_SIMULATED |
| `mach_zehnder_phase_scan` | Three-pulse MZ fringe, visibility, shot-noise sensitivity | FULLY_SIMULATED |
| `gravity_sweep` | Gravimeter response curve (hybrid, or emergent with `gravity_propagation: true`; optional emergent gradient via `gravity_gradient_per_m`) | HYBRID / FULLY_SIMULATED |
| `vibration_sensitivity_sweep` | Mirror-motion response - sinusoidal amplitude axis, or `vibration_model: time_domain` for Peterson-series motion with the Cheinet budget check | HYBRID / FULLY_SIMULATED |
| `multi_drop_cycle` | N-drop campaign with noise budget, correlated seismic vibration, projection noise, servo, Allan deviation | FULLY_SIMULATED |

Add `raman_substeps: N` (N > 1) to any emergent-mode study to integrate the
finite-duration Raman pulses sub-pulse. See
[docs/AISIM_GRAVIMETER_STUDIES.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/AISIM_GRAVIMETER_STUDIES.md)
for the scientific meaning and scope of each study.

```bash
# Run the classic three studies (hybrid mode)
scripts/run_aisim_gravimeter_studies.sh
```

### Programmatic use - multi-drop measurement cycle

```python
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle

result = run_aisim_multi_drop_cycle(
    n_drops=100,               # 100 drops
    cycle_time_s=1.0,          # 1 Hz cycle rate
    gravity_true_m_s2=9.81,
    gravity_propagation=True,  # emergent-gravity mode
    raman_substeps=8,          # sub-pulse finite-τ Raman integration
    detection_noise_enabled=True,
    n_detected_per_drop=1000,
    projection_noise=True,     # emergent Monte-Carlo quantum projection noise
    correlated_vibration=True, # drops share one continuous Peterson seismic series
    servo_enabled=True,        # closed-loop fringe lock
    servo_gain=0.5,
)

print(f"Mean g = {result['mean_g_m_s2']:.9f} m/s^2")
print(f"Allan deviation at tau=1s: {result['allan_dev_m_s2'][0]:.2e}")
```

---

## Bench modes

### `virtual`
Synthetic interferometer I/Q data with configurable displacement signals,
noise, and drift. Known ground truth enables algorithm accuracy measurement
(RMSE, MAE, SNR, PSD correlation).

### `real`
Real interferometer-style CSV input with `I_meas`, `Q_meas` columns and
optional `x_true` for validation.

### `real_gravity`
Real gravimetry time-series ingestion supporting `.ggp` files, `.zip`
archives, directories of `.ggp` files, or pre-converted CSV. Includes gap
detection, longest-contiguous-segment analysis, and dropped-row tracking.

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
- **Shot-noise sensitivity** - `1/(C · k_eff · T² · √(N/T_cycle))` in m/s²/√Hz and µGal/√Hz
- **Systematic effects** - gravity gradient shift, Coriolis shift (order-of-magnitude estimates)
- **Output format version** - `qgrav_output_format_version: "1.0"` for downstream consumers
- **Corrections metadata** - `data_product_level_at_analysis`, `corrections_applied`, `correction_metrics` (when corrections enabled)
- Gap report (for real gravity data)

---

## Physics & analysis toolbox

### Shot-noise sensitivity
The quantum projection noise limit for atom interferometer gravimeters:

```
delta_g = 1 / (C · k_eff · T² · √(N / T_cycle))
```

Available as `shot_noise_sensitivity_m_s2_per_sqrt_hz()` and
`sensitivity_ugal_per_sqrt_hz()` in `qgrav.physics`. In the multi-drop cycle
the floor can instead **emerge** from per-drop `Binomial(N_det, P)` draws
(`projection_noise: true`).

### Sensitivity function and vibration transfer function

The three-pulse Mach-Zehnder sensitivity function g_s(t) (Cheinet 2008)
quantifies how laser-phase or mirror-vibration perturbations translate into
interferometer phase shift:

- `sensitivity_function_time_domain()` - time-domain g_s(t) for instantaneous or finite-duration pulses
- `transfer_function_vibration()` - |G(2πf)|² with notches at f = n/T and 1/f² rolloff
- `acceleration_to_phase_transfer_function_sq()` - |H_a(2πf)|² for acceleration PSD input
- `integrate_vibration_noise()` - broadband integrator returning equivalent gravity noise σ_g

Built-in Peterson 1993 NLNM/NHNM seismic noise models serve as reference
acceleration PSDs. The vibration sweep's `time_domain` mode closes the loop:
mirror motion synthesized from these PSDs is fed through the actual pulse
sequence and the realized phase noise is checked against the integrated
budget on every run.

### Gravity gradient - estimate and emergent physics

`qgrav.physics.systematics` provides order-of-magnitude report-level
estimates (gravity gradient, Coriolis). The gradient is also real simulation
physics: `gravity_gradient_per_m` makes the propagator integrate the gradient
trajectory, and `qgrav.physics.phase_models.gravity_gradient_phase_rad`
provides the matching Peters/Chung/Chu closed form
`k_eff·γ·T²·[(z₀−z_ref) + v₀T − (7/12)gT²]` used by the cross-validation
tests.

### Noise type identification

Two complementary methods, both stored in `metrics.json`:

- **ACF method (primary)** - lag-1 autocorrelation (Riley 2004) applied
  directly to the time series; robust for mixed noise types.
- **Slope method (legacy)** - log-log slope of the Allan curve, classifying
  white/flicker phase, white/flicker frequency, and random-walk frequency
  noise.

### Real-gravimetry residual chain (tide, pressure, polar motion, ocean loading)

For IGETS Level 1 or Level 2 data, enable `apply_corrections: true` in
`bench_real_gravity` to run the standard superconducting-gravimeter residual
chain, in order:

1. **Solid-earth body tide** - PyGTide (if installed) or internal 20-constituent HW95 model (~50 nGal RMS truncation error)
2. **Atmospheric pressure loading** - linear admittance model (-3 nm/s²/hPa default, Crossley 1995)
3. **Polar motion (pole tide)** - from user-supplied IERS C04 pole coordinates and the IERS gravimetric δ factor *(off by default)*
4. **Ocean tidal loading** - from user-supplied Onsala-BLQ constituent amplitudes and phases *(off by default)*

Each stage follows the `corrected = observed − effect` convention, is fully
offline, and is recorded in `metrics.json`. The pipeline auto-detects the
IGETS data-product level from the sample rate and never double-corrects
already-reduced Level-3 residuals. See
[docs/REAL_GRAVITY_DATA.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/REAL_GRAVITY_DATA.md).

### Published references

Frozen registry of **14** benchmark values with DOI links, used directly by
the automated validation suite:

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

The registry audits itself: every historical value/unit correction is kept
in-code (`_V1_0_0_VALUE_BUGS`, `_V1_0_1_VALUE_BUGS`) so stale downstream
numbers can be traced to their fix.

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
    physics/                    # constants, phase models (incl. gradient closed form),
                                # sensitivity function, noise models, readout/servo, systematics
    pipeline/                   # run orchestration (interferometer, gravity, simulation, plots)
    reporting/                  # HTML report generation (Jinja2, secret-redacting)
    sim_ai/                     # AISim adapter layer
      aisim_adapter.py          #   facade re-exporting the split adapter modules
      _adapter_core.py          #   shared cloud/pulse helpers, fringe calibration
      _scans.py / _sweeps.py    #   Rabi, MZ, gravity & vibration sweeps (sinusoidal/time-domain)
      _multi_drop.py            #   multi-drop cycle, projection noise, servo
      _config_run.py            #   YAML-driven study dispatch
      _aisim_overrides.py       #   gravity/gradient propagator, chirped wavevectors, sub-pulse
    validation/                 # published references (14 entries), per-paper setups,
                                # QuTiP cross-check, truth checks, curve comparison
    vendor/aisim/               # vendored AISim atom-optics core (checksum-guarded)
    vendor/allantools/          # vendored Allan-deviation statistics (checksum-guarded)
    gui/                        # tkinter desktop application (6 tabs incl. Validation)
    config.py                   # YAML loading + validation
    visuals.py                  # matplotlib figure builders
    cli.py                      # CLI entry point (run, gui, convert-ggp, validate-data, info)
  tests/                        # 490 tests (pytest)
```

---

## Tests

```bash
# Headless matplotlib backend (avoids tkinter display issues)
# PowerShell:
$env:MPLBACKEND = "Agg"
# Bash:
export MPLBACKEND=Agg

# Fast suite (what CI runs on every push/PR)
python -m pytest -q -m "not slow"

# Published-reference simulation regressions (nightly in CI)
python -m pytest -q -m slow

# Performance micro-benchmarks (needs qgrav[benchmark])
python -m pytest tests/benchmark_aisim.py -m benchmark -q
```

**490 tests** run green on Linux and Windows (Python 3.11-3.13) with a
coverage ratchet at 78 % (suite sits at ~82 %). Guards go beyond unit checks:
byte-level checksums pin the vendored AISim/allantools trees, a wall-clock
performance guard catches complexity regressions, published-reference values
are pinned test-by-test with their unit conversions, and CI meta-tests parse
the workflow files themselves.

---

## Documentation

| Document | Description |
|----------|-------------|
| **[Online documentation](https://adityagit94.github.io/Quantum-Gravitometer/)** | The full rendered documentation site (recommended). |
| [docs/COMPLETE_GUIDE.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/COMPLETE_GUIDE.md) | The complete user guide: install, run, configure, interpret results. |
| [CHANGELOG.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/CHANGELOG.md) | Full change log. |
| [GUIDE.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/GUIDE.md) | Quick-start workflow guide. |
| [docs/V1_PHYSICS_UPGRADE.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/V1_PHYSICS_UPGRADE.md) | Emergent-physics design and equations. |
| [docs/PHYSICS_REVIEW_PACKET.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/PHYSICS_REVIEW_PACKET.md) | **Comprehensive review packet for external atom-interferometry experts** (with executable notebook `docs/reviewer_notebook.ipynb`) |
| [docs/ARCHITECTURE.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/ARCHITECTURE.md) | System architecture overview |
| [docs/SCIENTIFIC_HARDENING.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/SCIENTIFIC_HARDENING.md) | What is AISim-backed vs. hybrid vs. analytic |
| [docs/AISIM_INTEGRATION.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/AISIM_INTEGRATION.md) | AISim vendor integration details |
| [docs/AISIM_GRAVIMETER_STUDIES.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/AISIM_GRAVIMETER_STUDIES.md) | Scientific meaning of each AISim study |
| [docs/REAL_GRAVITY_DATA.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/REAL_GRAVITY_DATA.md) | Real gravimetry data ingestion and corrections guide |
| [docs/GUI.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/GUI.md) | Desktop GUI documentation |
| [docs/REPRODUCTION.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/REPRODUCTION.md) | Reproducing pipeline runs |
| [docs/ROADMAP_V1_TO_V2.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/docs/ROADMAP_V1_TO_V2.md) | Current status and where the project is headed |
| [CONTRIBUTING.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/CONTRIBUTING.md) | Dev setup, tests, code style, PR flow |
| [SECURITY.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/SECURITY.md) · [CODE_OF_CONDUCT.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/CODE_OF_CONDUCT.md) | Security policy · community standards |

---

## Contributing & citing

Contributions are welcome - see [CONTRIBUTING.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/CONTRIBUTING.md)
for dev setup, the test commands, and the project's guiding principles, and
[CODE_OF_CONDUCT.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/CODE_OF_CONDUCT.md).
Report bugs and request features via the GitHub issue templates; report
vulnerabilities privately per [SECURITY.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/SECURITY.md).

If you use qgrav in academic work, please cite it via the **"Cite this
repository"** button on GitHub (backed by [CITATION.cff](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/CITATION.cff)).
Each release is archived on Zenodo; cite the concept DOI
[10.5281/zenodo.20618573](https://doi.org/10.5281/zenodo.20618573), which
always resolves to the latest version.

qgrav vendors [AISim](https://github.com/bleykauf/aisim) (GPL-3.0) and
[allantools](https://github.com/aewallin/allantools) (LGPL-3.0); see
[`src/qgrav/vendor/ATTRIBUTION.md`](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/src/qgrav/vendor/ATTRIBUTION.md).

---

## Dependencies

| Package | Version | Used by |
|---------|---------|---------|
| numpy | >= 1.23 | Core |
| matplotlib | >= 3.7 | Core |
| pyyaml | >= 6.0 | Core |
| jinja2 | >= 3.1 | Core (reporting) |
| scipy | >= 1.6 | Core (improved estimator) + vendored allantools and aisim |
| qutip | >= 4.7 | Optional (`pip install qgrav[qutip]`) - independent cross-check |

---

## What's new

**v1.6.0** - emergent gradient physics and end-to-end vibration validation:

- **Emergent gravity-gradient physics** - the propagator integrates a linear
  gradient to first order in γ and the emergent phase matches the
  Peters/Chung/Chu `(7/12)·γ·g·T⁴` closed form to ~0.1 %.
- **Time-domain mirror motion** (`vibration_model: "time_domain"`) - Peterson
  seismic series through the actual pulse sequence, truth-checked against the
  integrated Cheinet budget on every run.
- Hardening: checksum-pinned vendored trees, secret-redacting HTML reports,
  non-blocking GUI station previews, vectorized offset tracking, and an
  even-window smoothing fix.

**The v1.5.x line** centred on emergent pulse physics and a complete residual
chain:

- **Sub-pulse Raman integration** (`raman_substeps`) - finite-τ pulses
  integrated as composed slices, converging to the Bertoldi 2019 closed form.
- **Emergent Monte-Carlo quantum projection noise** (`projection_noise`) -
  the shot-noise floor emerges from per-drop `Binomial(N_det, P)` statistics,
  matching the analytic limit to 0.2 %.
- **Polar-motion and ocean-loading reductions** complete the standard SG
  residual chain (tide → pressure → polar motion → ocean loading).
- **Multi-run Allan-curve comparison** in the GUI Results tab.

Earlier releases added multi-drop measurement cycles with a fringe-lock servo,
one-click reproductions of five published transportable gravimeters, an
independent **QuTiP** cross-check, real **IGETS** superconducting-gravimeter
analysis, and the six-tab desktop **GUI**.

See **[CHANGELOG.md](https://github.com/adityagit94/Quantum-Gravitometer/blob/main/CHANGELOG.md)**
for the complete, version-by-version history.
