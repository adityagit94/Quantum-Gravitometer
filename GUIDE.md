# qgrav Guide

This guide explains how to use the project in a clean, research-oriented way.

## 1) What this project is

This is **not** a hardware gravimeter. It is a **software research platform** with three lanes:

1. **Simulation lane** — atom-optics / interferometer simulation
2. **Virtual bench lane** — synthetic interferometer readout and estimator testing
3. **Real gravimetry lane** — real gravity residual data analysis from public datasets

The third lane is the most important when you do not have hardware.

---

## 2) Recommended working order

### Phase A — make the real-data lane reliable
Use one station file first. Make sure the parser, plots, and statistics are correct. For IGETS Level 1 or Level 2 data, enable `apply_corrections: true` in `bench_real_gravity` so that tides and pressure effects are removed before stability analysis.

### Phase B — compare stations
Once one station works, compare several stations and document differences in drift, gaps, and long-term stability.

### Phase C — tie this to the simulation lane
Use the same reporting language (PSD, Allan, summary metrics) for both simulated and real data.

### Phase D — noise budget via sensitivity function (v0.8)
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

### Data Browser tab
Use it to:
- choose a dataset source
- scan station codes
- preview one station
- inspect metadata and gap statistics
- create a ready-to-run config from the selected station

### Experiment tab
Use it to:
- choose the bench mode
- tune statistics backend
- point to the gravity source and station
- enable/disable AISim
- push the settings back into YAML

### Results tab
Use it to:
- inspect `metrics.json`
- view interactive plots
- open HTML report and run artifacts

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


## Phase 2 — AISim gravimeter studies

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
