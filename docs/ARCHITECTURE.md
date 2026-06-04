# Architecture (v1.0.0)

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
- `src/qgrav/physics/noise_models.py` — white noise, random walk, outlier injection,
  **time-domain vibration generator (v1.0)**, **detection noise (v1.0)**,
  **spontaneous emission probability (v1.0)**
- `src/qgrav/physics/readout_models.py` — output port population models,
  **fringe-locking servo integrator (v1.0)**
- `src/qgrav/physics/ground_truth.py` — reference relationships for truth-checking

### 2. Simulation layer

- `src/qgrav/sim_ai/aisim_adapter.py` — wraps vendored AISim. Functions:
  - `run_aisim_rabi_scan`
  - `run_aisim_mach_zehnder_phase_scan`
  - `run_aisim_gravity_sweep` (hybrid OR fully simulated via `gravity_propagation` **v1.0**)
  - `run_aisim_vibration_sensitivity_sweep` (hybrid OR fully simulated **v1.0**)
  - `run_aisim_multi_drop_cycle` **v1.0** — N independent drops with optional detection noise, servo, Allan deviation
  - `_run_mach_zehnder_sequence_with_gravity` **v1.0** — emergent-gravity MZ
  - `_calibrate_gravity_phase_offset` **v1.0** — per-sweep pulse-timing offset calibration
  - `_build_wavefront` **v1.0** — Zernike wavefront constructor
  - `_allan_deviation` **v1.0** — overlapping Allan deviation for the multi-drop time series
- `src/qgrav/sim_ai/simple_ai.py` — lightweight simulation fallback

### 3. Vendored AISim (patched)

- `src/qgrav/vendor/aisim/prop.py`:
  - `Propagator`, `FreePropagator` (upstream)
  - **`GravityFreePropagator`** (v1.0) — exact ballistic kinematics under uniform g with optional linear gradient
  - **`TwoLevelTransitionPropagator`** (patched v1.0): replaces `exp(-i·δ·t₀)` with `exp(-i·(-k_eff·z(t₀) + ½·chirp·t₀²))`; adds optional `single_photon_detuning_hz` for AC Stark
  - `SpatialSuperpositionTransitionPropagator` (forwards AC Stark to the 2-level base class)
- `src/qgrav/vendor/aisim/beam.py`:
  - **`Wavevectors`** (patched v1.0) — accepts `chirp_rate_rad_per_s2`; `doppler_shift` returns `-v·k_eff + chirp·atoms.time`
  - `IntensityProfile`, `Wavefront` (now actively wired)
- `src/qgrav/vendor/aisim/__init__.py` — exports `GravityFreePropagator` (v1.0)

### 4. Bench layer (data sources)

- `src/qgrav/bench_ifo/virtual_ifo.py` — synthetic I/Q signal generator
- `src/qgrav/bench_ifo/real_ifo.py` — CSV reader for real interferometer data
- `src/qgrav/bench_ifo/real_gravity.py` — wrapper for gravimetry dataset loading

### 5. Datasets layer

- `src/qgrav/datasets/gravimetry.py` — GGP parsing, station metadata, gap detection, CSV conversion
- `src/qgrav/datasets/corrections.py` — tide + pressure corrections, IGETS level detection
- `src/qgrav/datasets/_tides_hw95.py` — 20-constituent simplified Wenzel HW95 tidal model

### 6. Estimation layer

- `src/qgrav/algorithms/baseline.py` — arctangent demodulation with global offset subtraction
- `src/qgrav/algorithms/improved.py` — adaptive offset tracking (EWMA) + Savitzky-Golay phase smoothing

### 7. Metrics layer

- `src/qgrav/metrics/allan.py` — overlapping Allan deviation (custom + allantools), noise ID (ACF + slope), Allan minimum
- `src/qgrav/metrics/psd.py` — power spectral density (Welch + periodogram)
- `src/qgrav/metrics/error_stats.py` — RMSE, MAE, SNR, bias computation

### 8. Validation layer

- `src/qgrav/validation/published_references.py` — 12-entry benchmark registry with DOI links, deprecation shims
- `src/qgrav/validation/truth_checks.py` — per-study pass/fail checks. Now handles:
  - `rabi_scan`, `mach_zehnder_phase_scan` (upstream)
  - `gravity_sweep` — branches on `gravity_propagation`; hybrid uses analytical-phase match, simulated uses visibility/scope (v1.0)
  - `vibration_sensitivity_sweep`
  - **`multi_drop_cycle`** (v1.0) — n_drops, finite, monotonic timestamps, |mean(g) − g_true|, Allan consistency
- `src/qgrav/validation/curve_comparison.py` — R-squared, Pearson correlation

### 9. Orchestration and reporting

- `src/qgrav/pipeline.py` — main orchestrator: corrections stage, output_format_version, connects all layers
- `src/qgrav/config.py` — YAML loading, validation (including corrections/IGETS keys, **gravity_propagation, multi_drop_cycle keys v1.0**)
- `src/qgrav/reporting/report.py` — HTML report generation (study-scope panel, corrections section, level banner)
- `src/qgrav/visuals.py` — matplotlib figure builders
- `src/qgrav/cli.py` — CLI entry point (`run`, `gui`, `convert-ggp`, `validate-data`)

### 10. GUI layer

- `src/qgrav/gui/app.py` — main tkinter application (~2100 lines), six tabs:
  Setup & Run, Data Browser, Config Editor, Results & Visuals, Validation, Guides.
  The Validation tab imports `qgrav.validation` lazily for the published-reference
  registry, the one-click paper reproductions, and the QuTiP cross-check.
- `src/qgrav/gui/widgets/` — MetricCards, ScrollableFrame, Tooltip, CollapsibleSection

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
    |                                  |
    |                                  +-- gravity_sweep (hybrid OR gravity_propagation)
    |                                  +-- vibration_sensitivity_sweep
    |                                  +-- multi_drop_cycle (v1.0)
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

## Pipeline flow — gravity_sweep with `gravity_propagation: true` (v1.0)

```
config.yaml { simulation.model: gravity_sweep, simulation.gravity_propagation: true }
    |
    v
run_aisim_gravity_sweep(gravity_propagation=True)
    |
    +-- chirp_rate = -k_eff * gravity_center_m_s2
    +-- Wavevectors(k1, k2, chirp_rate_rad_per_s2=chirp_rate)
    +-- phase_bias_rad = pi/2  (just the mid-fringe offset; no gravity term)
    |
    +-- _calibrate_gravity_phase_offset(...)  --> sim_phase_offset
    |       (one fringe scan at g=gravity_center to find pulse-timing residual)
    |
    +-- for each g in gravity_values:
    |        _run_mach_zehnder_sequence_with_gravity(
    |            g_m_s2=g,
    |            final_phase_rad=phase_bias_rad,
    |            phase_offset_rad=sim_phase_offset,
    |        )
    |        # Inside: bs1 -> GravityFreePropagator(T) -> mirror
    |        #         -> GravityFreePropagator(T) -> bs2(phase_scan = pi/2 + sim_phase_offset)
    |        # The MZ matrix elements multiply through, producing
    |        # phi_MZ = k_eff * (g - g_chirp) * T^2 + pi/2 + (residual that calibration removes)
    |
    v
result["study_scope_category"] = "FULLY_SIMULATED"
result["physical_model"]       = "AISim + GravityFreePropagator + chirped Wavevectors"
truth_checks                   = { fringe_visibility > 0.3, study_scope_fully_simulated }
```

---

## Pipeline flow — multi_drop_cycle (v1.0)

```
config.yaml { simulation.model: multi_drop_cycle, n_drops: 100, ... }
    |
    v
run_aisim_multi_drop_cycle(...)
    |
    +-- (optional) one-shot calibration like the gravity sweep
    +-- phase_bias_rad based on gravity_propagation flag
    |
    +-- for i in range(n_drops):
    |        _create_detected_ensemble(seed=base_seed + i + 1)
    |        out = _run_mach_zehnder_sequence_with_gravity(
    |            g_m_s2=gravity_true_m_s2,
    |            final_phase_rad=phase_bias_base + servo_phase_correction,
    |            phase_offset_rad=sim_phase_offset,
    |        )
    |        p3_raw[i] = out["port_3"]
    |
    |        if detection_noise_enabled:
    |            p3_noisy[i] = p3_raw[i] + N(0, 1/sqrt(N_detected))
    |
    |        g_estimates[i] = g_true + (p3_noisy[i] - 0.5) / fringe_slope
    |
    |        if servo_enabled:
    |            servo_phase_correction = servo_integrator_step(
    |                p3_noisy[i], servo_phase_correction, setpoint=0.5, gain=...
    |            )
    |
    +-- taus, adev = _allan_deviation(g_estimates, cycle_time_s)
    |
    v
result["g_estimates_m_s2"], result["allan_taus_s"], result["allan_dev_m_s2"]
truth_checks = { n_drops_matches, mean_close_to_true_gravity, allan_dev_decreasing, ... }
```

---

## Module dependency rules

- `physics/` has **no imports** from other qgrav packages (self-contained)
- `vendor/aisim/` has **no imports** from other qgrav packages (vendored upstream + local patches)
- `datasets/` imports only from `physics/` (for `_tides_hw95` using constants)
- `metrics/` imports only from `vendor/allantools`
- `validation/` imports only from `physics/`
- `sim_ai/aisim_adapter.py` imports from `physics/` (constants, phase models, noise_models, readout_models), `vendor/aisim/`, and `validation/truth_checks`
- `pipeline.py` imports from all layers (it is the orchestrator)
- `gui/` imports from `pipeline`, `config`, and `visuals`
