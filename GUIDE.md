# qgrav Guide

This guide explains how to use the project in a clean, research-oriented way.

## 1) What this project is

This is **not** a hardware gravimeter. It is a **software research platform** with three lanes:

1. **Simulation lane** - atom-optics / interferometer simulation
2. **Virtual bench lane** - synthetic interferometer readout and estimator testing
3. **Real gravimetry lane** - real gravity residual data analysis from public datasets

The third lane is the most important when you do not have hardware.

---

## 2) Recommended working order

### Phase A - make the real-data lane reliable
Use one station file first. Make sure the parser, plots, and statistics are correct. For IGETS Level 1 or Level 2 data, enable `apply_corrections: true` in `bench_real_gravity` so that tides and pressure effects are removed before stability analysis.

### Phase B - compare stations
Once one station works, compare several stations and document differences in drift, gaps, and long-term stability.

### Phase C - tie this to the simulation lane
Use the same reporting language (PSD, Allan, summary metrics) for both simulated and real data.

### Phase D - noise budget via sensitivity function (v0.8)
Use `integrate_vibration_noise()` with the Peterson NLNM/NHNM models to estimate what fraction of your real-data noise comes from seismic vibrations vs. instrument-intrinsic noise. Compare to the shot-noise sensitivity from your AISim simulation.

---

## 3) Clean project rules

- Keep **all experiment parameters** in YAML configs.
- Never hardcode station codes in Python.
- Each run must create a new folder under `runs/`.
- Never overwrite previous results.
- Use the bundled sample first before pointing to large archives.
- Run `pytest -q` before packaging or reporting results.

---

## 4) Real gravimetry lane

### Supported source types
- directory of `.ggp` files
- `.zip` archive of `.ggp` files
- a single `.ggp` file
- converted CSV

### What the loader does
- parses the series
- sorts timestamps
- estimates the nominal sampling interval
- detects duplicates, reversals, and gaps
- estimates missing samples
- selects the **longest contiguous segment** for PSD/Allan analysis

### Why longest contiguous segment?
PSD and Allan deviation assume regularly sampled data. If the full record has gaps, using the longest continuous segment is a safer default than silently filling missing values.

---

## 5) GUI workflow

Launch with `qgrav gui` (or `qgrav-gui`). The window has six tabs.

### Setup & Run tab
Configure a run through visual controls (kept in sync with the YAML editor):
- pick a workflow (`real_data`, `synthetic`, `advanced`) - the form hides
  controls that do not apply
- choose the bench mode and statistics backend
- point to a gravity source and station, or enable AISim and pick a study model
- for synthetic runs, set atom/pulse parameters, and (in the collapsible
  sections) the advanced physics and the multi-drop noise budget + servo
- push settings back into the YAML with **Apply controls to editor**

### Data Browser tab
- choose a dataset source (or **Use sample** for the bundled IGETS station)
- scan station codes; preview one station
- inspect metadata and gap statistics
- create a ready-to-run config, or send the selection to Setup

### Config Editor tab
The raw YAML - the ground truth for what actually runs. Validate and Save As here.

### Results & Visuals tab
- inspect `metrics.json` in a tree and the metric cards
- view interactive plots (single plots first, then the dashboard)
- open the HTML report and run artifacts

### Validation tab
- browse the published-reference registry (with sources and DOIs)
- one-click reproductions of Freier 2016, Hu 2013, Ménoret 2018, Xu 2022, Wu 2019
  (each builds and runs a `multi_drop_cycle` config from that paper's parameters)
- run the QuTiP / analytic cross-checks of the single-pulse dynamics

### Guides tab
A navigable in-app guide (quick start, study models, noise & realism, validation,
interpreting results, **how to move ahead**, glossary, common mistakes) plus links
that open the on-disk project documents.

---

## 6) What to report for real gravimetry runs

For each station, at minimum report:
- station code
- date span
- number of samples
- median sample spacing
- gap count
- missing-sample estimate
- longest contiguous segment length
- PSD
- Allan deviation
- histogram
- summary statistics (mean, std, min, max)

---

## 7) What this does *not* prove

A real gravimetry run does **not** prove that an atom gravimeter was built or tested. It proves that:

- your data pipeline is correct,
- your stability analysis is functioning,
- your reporting is reproducible,
- your platform can handle real precision time series.

That is still valuable and legitimate.

---

## 8) Suggested milestone after this stage

The best next scientific milestone is:

> validate that your corrections-enabled real-data Allan deviations are consistent with published SG noise floors, and compare the vibration-limited sensitivity from the sensitivity function against your AISim shot-noise sensitivity.


## Phase 2 - AISim gravimeter studies

The project now includes three gravimeter-oriented AISim studies. Use them in this order:

1. **Mach–Zehnder phase scan**
   - proves the three-pulse interferometer fringe exists under the chosen ensemble/beam settings
2. **Gravity sweep**
   - shows how the interferometer output changes with small gravity changes around an operating point
3. **Vibration sensitivity sweep**
   - shows how reference-mirror motion translates into phase error and equivalent gravity error

Recommended workflow:

```bash
qgrav run --config configs/example_aisim_phase_scan.yaml
qgrav run --config configs/example_aisim_gravity_sweep.yaml
qgrav run --config configs/example_aisim_vibration_sweep.yaml
```

Then compare the three reports and quote them carefully:
- phase scan = fringe quality / visibility
- gravity sweep = gravimeter response curve
- vibration sweep = sensitivity to motion-induced phase error

For full interpretation, read `docs/AISIM_GRAVIMETER_STUDIES.md`.


## Phase 3 - Fully simulated and multi-drop studies (v1.0)

v1.0 unlocks two new workflows on top of the existing study models. They are aimed at users who want a self-consistent numerical gravimeter rather than the analytical-phase hybrid.

### 3.1 Fully simulated gravity / vibration sweeps

Any `gravity_sweep` or `vibration_sensitivity_sweep` config can be promoted from `HYBRID` to `FULLY_SIMULATED` by adding a single key to the simulation block:

```yaml
simulation:
  enabled: true
  backend: aisim
  model: gravity_sweep            # or vibration_sensitivity_sweep
  gravity_propagation: true       # NEW in v1.0
  # optional:
  # gravity_gradient_per_m: 3.086e-6   # free-air gradient
  # ... existing AISim keys ...
```

Internally this swaps `FreePropagator` for a `GravityFreePropagator`, chirps the Raman laser to track gravity, and uses the patched integrated-phase formula. The gravity phase comes out of the simulation rather than from a closed-form formula. See `docs/V1_PHYSICS_UPGRADE.md` for the full derivation.

The HTML report's study-scope panel will turn from amber (HYBRID) to green (FULLY_SIMULATED) and the truth checks will switch from "exact match to analytic phase" to "visibility > 0.3 and FULLY_SIMULATED scope".

### 3.2 Multi-drop measurement cycle

This is a new study model that simulates a full N-drop gravimeter campaign:

```yaml
simulation:
  enabled: true
  backend: aisim
  model: multi_drop_cycle
  n_drops: 100
  cycle_time_s: 1.0
  gravity_true_m_s2: 9.81
  gravity_propagation: true
  detection_noise_enabled: true
  n_detected_per_drop: 1000
  servo_enabled: true
  servo_gain: 0.5
```

Output keys include `g_estimates_m_s2`, `timestamps_s`, `mean_g_m_s2`, `std_g_m_s2`, `allan_taus_s`, `allan_dev_m_s2`. The Allan deviation can be compared directly against published SG noise floors and your real-data Allan plots from `bench_real_gravity`. Use this to characterise the simulated sensitivity floor and the expected behaviour of the servo loop before any hardware exists.

### 3.3 Time-domain vibration noise

Programmatically generate hour-long realistic acceleration / displacement traces matching Peterson NLNM or NHNM:

```python
from qgrav.physics.noise_models import generate_vibration_timeseries
ts = generate_vibration_timeseries(
    duration_s=3600.0,
    sample_rate_hz=100.0,
    seismic_model="nlnm",
    isolation_cutoff_hz=1.0,   # second-order high-pass filter
    seed=42,
)
# ts["accel_m_s2"], ts["velocity_m_s"], ts["displacement_m"]
```

### 3.4 Advanced systematics

Pass `single_photon_detuning_hz` to any `TwoLevelTransitionPropagator` (or `SpatialSuperpositionTransitionPropagator`) to enable the AC Stark / light-shift correction. For wavefront aberrations, use `_build_wavefront(coeff_dict, r_wf)` and pass the result via the `wavefront` kwarg of `_run_mach_zehnder_sequence`.

See `docs/V1_PHYSICS_UPGRADE.md` for the equations and design rationale.


## Scientific hardening

The simulation layer now separates:
- atom source
- pulse sequence
- phase model
- readout model
- ground-truth validation

See `docs/SCIENTIFIC_HARDENING.md` for details on what is fully AISim-backed, what is hybrid, and how truth-checks are stored in reports.


## Corrections workflow (v0.8)

For IGETS Level 1 or Level 2 data, the raw gravity residual contains the body-tide signal (~100 uGal amplitude) which dominates any instrument noise. To get meaningful Allan deviation results:

1. Set `apply_corrections: true` in your `bench_real_gravity` config section
2. The pipeline auto-detects the IGETS level from sample rate (or set `igets_level: "1"` to force)
3. Solid-earth body tide is subtracted (PyGTide if installed, else internal 20-constituent HW95 model)
4. If `pressure_csv_path` is provided, atmospheric pressure admittance is applied (-3 nm/s^2/hPa default)
5. The corrected series is used for all downstream PSD/Allan/noise-ID computation
6. `metrics.json` records what was applied, which backend was used, and the RMS of each subtracted signal

This makes IGETS Allan deviation results comparable to published SG noise floors (which assume Level 3 processing).

See `docs/REAL_GRAVITY_DATA.md` for configuration keys and backend details.
