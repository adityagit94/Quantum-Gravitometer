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
Use one station file first. Make sure the parser, plots, and statistics are correct.

### Phase B — compare stations
Once one station works, compare several stations and document differences in drift, gaps, and long-term stability.

### Phase C — tie this to the simulation lane
Use the same reporting language (PSD, Allan, summary metrics) for both simulated and real data.

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

> add a gravimeter-style AISim mode and compare its stability/phase outputs to the same reporting framework used for the real gravimetry lane.


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
