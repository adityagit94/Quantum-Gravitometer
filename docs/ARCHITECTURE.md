# Architecture (v0.8.0)

## Layered design

### 1. Physics layer

Single source of truth for physical constants, interferometer models, and noise floor references.

- `src/qgrav/physics/constants.py` — frozen `PhysicalConstant` registry (CODATA, Rb-87/Cs-133, geophysical)
- `src/qgrav/physics/sensitivity_function.py` — MZ sensitivity function g_s(t), transfer functions |G|² and |H_a|², vibration noise integrator
- `src/qgrav/physics/_seismic_models.py` — Peterson 1993 NLNM/NHNM acceleration PSD models
- `src/qgrav/physics/phase_models.py` — gravity phase, vibration phase, shot-noise sensitivity
- `src/qgrav/physics/systematics.py` — gravity gradient, Coriolis effect estimates (uses constants module)
- `src/qgrav/physics/atom_source.py` — atom cloud source/detector description
- `src/qgrav/physics/pulse_sequence.py` — Rabi and Mach-Zehnder timing helpers
- `src/qgrav/physics/noise_models.py` — white noise, random walk, outlier injection
- `src/qgrav/physics/readout_models.py` — output port population models
- `src/qgrav/physics/ground_truth.py` — reference relationships for truth-checking

### 2. Simulation layer

- `src/qgrav/sim_ai/aisim_adapter.py` — wraps vendored AISim for Rabi, phase scan, gravity/vibration sweeps; adds `study_scope` labels
- `src/qgrav/sim_ai/simple_ai.py` — lightweight simulation fallback

### 3. Bench layer (data sources)

- `src/qgrav/bench_ifo/virtual_ifo.py` — synthetic I/Q signal generator
- `src/qgrav/bench_ifo/real_ifo.py` — CSV reader for real interferometer data
- `src/qgrav/bench_ifo/real_gravity.py` — wrapper for gravimetry dataset loading

### 4. Datasets layer

- `src/qgrav/datasets/gravimetry.py` — GGP parsing, station metadata, gap detection, CSV conversion
- `src/qgrav/datasets/corrections.py` — tide + pressure corrections, IGETS level detection
- `src/qgrav/datasets/_tides_hw95.py` — 20-constituent simplified Wenzel HW95 tidal model

### 5. Estimation layer

- `src/qgrav/algorithms/baseline.py` — arctangent demodulation with global offset subtraction
- `src/qgrav/algorithms/improved.py` — adaptive offset tracking (EWMA) + Savitzky-Golay phase smoothing

### 6. Metrics layer

- `src/qgrav/metrics/allan.py` — overlapping Allan deviation (custom + allantools), noise ID (ACF + slope), Allan minimum
- `src/qgrav/metrics/psd.py` — power spectral density (Welch + periodogram)
- `src/qgrav/metrics/error_stats.py` — RMSE, MAE, SNR, bias computation

### 7. Validation layer

- `src/qgrav/validation/published_references.py` — 12-entry benchmark registry with DOI links, deprecation shims
- `src/qgrav/validation/truth_checks.py` — per-study pass/fail checks
- `src/qgrav/validation/curve_comparison.py` — R-squared, Pearson correlation

### 8. Orchestration and reporting

- `src/qgrav/pipeline.py` — main orchestrator: corrections stage, output_format_version, connects all layers
- `src/qgrav/config.py` — YAML loading, validation (including corrections/IGETS keys)
- `src/qgrav/reporting/report.py` — HTML report generation (study-scope panel, corrections section, level banner)
- `src/qgrav/visuals.py` — matplotlib figure builders
- `src/qgrav/cli.py` — CLI entry point (`run`, `gui`, `convert-ggp`)

### 9. GUI layer

- `src/qgrav/gui/app.py` — main tkinter application (1200+ lines)
- `src/qgrav/gui/widgets/` — extracted MetricCards, ScrollableFrame

---

## Pipeline flow (real_gravity path)

```
config.yaml
    |
    v
load_config() --> validate_config_structure()
    |
    v
run_pipeline()
    |
    +---> [virtual]       generate_virtual_ifo() --> algorithms --> error stats
    |
    +---> [real]          load_real_ifo_csv() --> algorithms --> error stats
    |
    +---> [real_gravity]  load_real_gravity_dataset() --> gap analysis
    |                         |
    |                         v
    |                     detect_igets_level()
    |                         |
    |                         v  (if apply_corrections: true)
    |                     apply_tide_correction() --> apply_pressure_correction()
    |
    +---> [if simulation.enabled]  run_aisim_*() --> study_scope labels
    |
    +---> allan_deviation_overlapping() --> identify_noise_type_acf()
    +---> compute_psd()
    |
    v
save outputs:
    metrics.json  (qgrav_output_format_version: "1.0")
    data.npz
    plots/
    SUMMARY.md
    report.html   (study-scope panel, corrections section, level banner)
```

---

## Module dependency rules

- `physics/` has **no imports** from other qgrav packages (self-contained)
- `datasets/` imports only from `physics/` (for `_tides_hw95` using constants)
- `metrics/` imports only from `vendor/allantools`
- `validation/` imports only from `physics/`
- `pipeline.py` imports from all layers (it is the orchestrator)
- `gui/` imports from `pipeline`, `config`, and `visuals`
