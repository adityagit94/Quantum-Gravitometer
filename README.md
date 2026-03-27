# qgrav — Software-first gravimeter R&D platform

`qgrav` is a **software-first research workbench** for gravimeter-related studies when hardware is unavailable. It combines:

- **atom simulation** (AISim-backed stage)
- **virtual interferometer data generation**
- **real gravimetry time-series ingestion** (`.ggp`, `.zip`, directory, or converted CSV)
- **PSD / Allan deviation analysis**
- **reproducible reports**
- **desktop GUI**

The project is designed for the realistic case where you cannot build or access a lab interferometer. Instead of making false hardware claims, it provides a clean research pipeline for:

1. simulation,
2. algorithm benchmarking,
3. public gravimetry dataset analysis,
4. reproducible reporting.

---

## What is new in this stage?

This stage adds a full **real gravimetry data lane**:

- `.ggp` parser for superconducting gravimeter residual files
- station metadata support from `SG station.txt`
- ZIP / directory / single-file ingestion
- gap detection and analysis-segment selection
- CSV conversion
- PSD / Allan / histogram / trend reporting
- GUI dataset browser for selecting and previewing stations
- per-station report generation

This is the correct validation path when hardware is out of scope.

---

## Repository layout

```text
qgrav/
  configs/
  data/
    raw/
      sg_sample/               # bundled sample station for testing the real-data lane
  docs/
  notebooks/
  scripts/
  src/qgrav/
    algorithms/
    bench_ifo/
    datasets/
    metrics/
    reporting/
    sim_ai/
    validation/
    visuals.py
    gui.py
    pipeline.py
  tests/
```

---

## Bench modes

### 1) `virtual`
Synthetic interferometer I/Q data with known truth displacement.

### 2) `real`
Real interferometer-style CSV input with `I_meas`, `Q_meas` and optional `x_true`.

### 3) `real_gravity`
Real gravimetry time-series input:
- `.ggp`
- `.zip` archive of `.ggp` files
- directory of `.ggp` files
- converted CSV

This mode is intended for superconducting gravimeter residual analysis.

---

## Quick start

### Install
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -U pip
pip install -e .
```

### Run the synthetic example
```bash
qgrav run --config configs/example.yaml
```

### Run the AISim example
```bash
qgrav run --config configs/example_aisim.yaml
```

### Run the real gravimetry example
```bash
qgrav run --config configs/example_real_gravity.yaml
```

### Launch the GUI
```bash
qgrav gui --config configs/example_real_gravity.yaml
```

### Convert a `.ggp` source to CSV
```bash
qgrav convert-ggp --source data/raw/sg_sample --station ap046 --out /tmp/ap046.csv
```

---

## Example outputs

Each run creates a timestamped folder under `runs/` with:

- `config_used.yaml`
- `data.npz`
- `metrics.json`
- `SUMMARY.md`
- `report.html`
- `plots/*.png`

---

## Real gravimetry workflow

1. Point `bench_real_gravity.source_path` to:
   - a `.zip` archive,
   - a directory of `.ggp` files,
   - a single `.ggp` file,
   - or a converted CSV.
2. Choose `station_code`.
3. Run the pipeline.
4. Inspect:
   - full trend plot,
   - histogram,
   - PSD,
   - Allan deviation,
   - gap report.

If gaps are present, the pipeline analyzes the **longest contiguous segment** by default and records the gap statistics in the report.

---

## Tests

Run all tests with:

```bash
pytest -q
```

Current stage includes tests for:
- synthetic pipeline
- AISim integration
- GUI import
- visual generation
- `.ggp` parsing
- CSV conversion
- real gravimetry pipeline

---

## Recommended next step after this stage

Once the real-data lane is stable, the next strongest upgrade is:

- a **gravimeter-relevant AISim study mode**
- gravity-phase scaling
- vibration sensitivity sweeps
- comparison between simulated stability and real gravimetry data signatures

See `GUIDE.md` and `docs/REAL_GRAVITY_DATA.md`.


## AISim gravimeter studies

The repo now includes three thesis/report-quality AISim studies:

- `configs/example_aisim_phase_scan.yaml` — full three-pulse Mach–Zehnder-style phase scan in AISim
- `configs/example_aisim_gravity_sweep.yaml` — hybrid gravity sweep using AISim for pulse-transfer effects and the standard gravimeter phase law for gravity
- `configs/example_aisim_vibration_sweep.yaml` — hybrid vibration sensitivity sweep using the three-pulse mirror-motion phase response

Run them with:

```bash
qgrav run --config configs/example_aisim_phase_scan.yaml
qgrav run --config configs/example_aisim_gravity_sweep.yaml
qgrav run --config configs/example_aisim_vibration_sweep.yaml
```

Or use:

```bash
scripts/run_aisim_gravimeter_studies.sh
```

See `docs/AISIM_GRAVIMETER_STUDIES.md` for the scientific meaning and limitations of each study.


## Scientific hardening

The simulation layer now separates:
- atom source
- pulse sequence
- phase model
- readout model
- ground-truth validation

See `docs/SCIENTIFIC_HARDENING.md` for details on what is fully AISim-backed, what is hybrid, and how truth-checks are stored in reports.
