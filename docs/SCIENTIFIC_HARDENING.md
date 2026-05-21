# Scientific hardening of the simulation layer

This stage restructures the gravimeter simulation code so that the physics and validation logic are easier to inspect, test, and explain in a thesis/report.

## Why this was added

A research-quality simulation platform should not hide the important scientific assumptions inside one large adapter or pipeline function. The simulation layer is now separated into explicit pieces:

- `src/qgrav/physics/atom_source.py` — source and detector description
- `src/qgrav/physics/pulse_sequence.py` — Rabi and Mach–Zehnder sequence helpers
- `src/qgrav/physics/phase_models.py` — gravity and vibration phase models
- `src/qgrav/physics/noise_models.py` — reusable stochastic perturbation functions
- `src/qgrav/physics/readout_models.py` — population/readout helpers
- `src/qgrav/physics/ground_truth.py` — reference relationships used for truth checking
- `src/qgrav/validation/truth_checks.py` — per-study pass/fail checks

## What is fully simulated and what is hybrid

### Fully AISim-backed
- `rabi_scan`
- `mach_zehnder_phase_scan`

These use AISim directly for the atom source, pulse propagation, and measured populations.

### Hybrid studies
- `gravity_sweep`
- `vibration_sensitivity_sweep`

These keep the AISim three-pulse sequence for pulse-transfer/contrast behavior, but inject the inertial phase analytically:

- gravity phase: `k_eff * g * T^2`
- vibration phase: `k_eff [z(0) - 2 z(T) + z(2T)]`

This is deliberate and should be stated honestly in reports.

## Ground-truth validation

Every AISim study now carries a `truth_checks` block in its result dictionary and in the saved `metrics.json` report output.

Examples:
- Rabi scan: occupation bounds, finite values, non-trivial response span
- Mach–Zehnder phase scan: bounded populations, sinusoidal fit quality
- Gravity sweep: exact match to the closed-form gravity phase relation used by the hybrid study
- Vibration sweep: exact match to the closed-form reference-mirror phase model and linearity in amplitude

These checks do not prove that the model matches hardware. They prove that the code behaves consistently with the equations it claims to implement.

## How to use this in your thesis/report

Describe the software as:

> a software-first gravimeter simulation and validation platform with explicit separation between atom source, pulse sequence, phase model, estimator/readout, and validation metrics.

Then be explicit about study scope:
- fully simulated,
- hybrid,
- or real-data only.

That honesty improves the quality of the project instead of weakening it.

## Additions in v0.7.0

### Shot-noise sensitivity
`phase_models.shot_noise_sensitivity_m_s2_per_sqrt_hz()` computes the quantum projection noise limit: `1/(C * k_eff * T^2 * sqrt(N/T_cycle))`. All three Mach-Zehnder AISim functions now report this in their output dictionaries and in the HTML report.

### Noise type identification
`metrics.allan.identify_noise_type()` fits a log-log slope to the Allan deviation curve and classifies the dominant noise process (white phase, flicker phase, white frequency, flicker frequency, or random walk). Allan plots are now annotated with the identified noise type.

### Allan minimum
`metrics.allan.allan_minimum()` locates the optimal averaging time (tau at minimum ADEV). Both pipeline paths report this in `metrics.json`.

### Systematic effects
`physics.systematics` provides order-of-magnitude estimates of the gravity gradient shift and the Coriolis effect. These are explicitly documented as NOT included in the AISim simulation and appear in the HTML report as a separate table.

### Published references
`validation.published_references` contains a registry of benchmark experimental values (Freier 2016, Menoret 2018, SG noise floor, MZ visibility) with a `compare_to_reference()` helper for tolerance-based comparison.

## Additions in v0.8.0

### Physical constants registry
New `physics/constants.py` provides a frozen `PhysicalConstant` dataclass (value, unit, source, uncertainty, note) for every constant used across the codebase. All previously hardcoded numerical literals in `systematics.py` (Earth rotation rate, free-air gradient, gravity defaults), `aisim_adapter.py` (Rb-87 D2 wavelength, gravity defaults), and `gui/app.py` have been replaced with imports from this module.

A regression test scans source files for stray numerical literals matching gravimetry patterns (`780e-9`, `7.2921e-5`, `3.086e-6`, `= 9.81`) and fails if any are found outside the constants module.

Key constants: `K_EFF_RB87_D2` (1.6105747e7 rad/m), `WAVELENGTH_RB87_D2` (780.241209686e-9 m), `OMEGA_EARTH` (7.2921150e-5 rad/s), `FREE_AIR_GRADIENT` (3.086e-6 /s^2/m), `NOMINAL_GRAVITY` (9.81 m/s^2), `STANDARD_GRAVITY` (9.80665 m/s^2).

### Sensitivity function (Cheinet 2008)
New `physics/sensitivity_function.py` implements the three-pulse Mach-Zehnder sensitivity function and vibration transfer function:

- **Time-domain g_s(t):** piecewise -1 on [0,T], +1 on [T,2T] for instantaneous pulses; linear ramps through each pulse for finite tau (Cheinet 2008 eqs. 7-10).
- **Laser-phase transfer function:** |G(2pif)|^2 = 16 sin^4(pi f T) / (2 pi f)^2. Notches at f = n/T, 1/f^2 rolloff above 1/T.
- **Acceleration-to-phase transfer function:** |H_a(2pif)|^2 = 16 k_eff^2 sin^4(pi f T) / (2 pi f)^4. Converts an acceleration PSD to interferometer phase variance.
- **Broadband integrator:** `integrate_vibration_noise()` takes an acceleration PSD on a frequency grid and returns sigma_phi (rad), sigma_g (m/s^2), and sigma_g (uGal) via trapezoidal integration.

### Peterson NLNM/NHNM seismic noise floor models
New `physics/_seismic_models.py` implements Peterson 1993 New Low/High Noise Models as piecewise log-log acceleration PSDs. These represent the envelope of global seismic background noise and serve as reference inputs for the vibration integrator. The models are adequate to a factor of two, which is below the uncertainty in site-specific coupling.

### Tide and pressure corrections
New `datasets/corrections.py` and `datasets/_tides_hw95.py` implement IGETS data corrections:

- **IGETS level detection:** Heuristic from sample rate (1 Hz -> Level 1, 1/60 Hz -> Level 2, 1/3600 Hz -> Level 3).
- **Tide correction:** PyGTide (full Wenzel catalogue, sub-microGal accuracy) is preferred when installed. The internal fallback uses 20 HW95 constituents (M2, S2, N2, K2, K1, O1, P1, Q1, Mf, Mm, plus 10 smaller) with Doodson-argument computation from UTC timestamps. Body-tide elasticity factor delta = 1.16 (Wahr-Dehant). Geographic amplitude factors: cos^2(lat) for semi-diurnal, sin(2*lat)/2 for diurnal. Truncation error ~50 nGal RMS vs full catalogue.
- **Pressure correction:** Linear admittance model (Crossley 1995): corrected = g - admittance * (p - p_ref). Default admittance: -3 nm/s^2/hPa.

Purpose: make IGETS Level 1 Allan deviations meaningful. Without corrections, the dominant signal is the body tide (~100 uGal amplitude), not instrument noise.

### ACF-based noise type identification
New `identify_noise_type_acf()` in `metrics/allan.py` wraps `allantools.ci.autocorr_noise_id` (Riley 2004 lag-1 autocorrelation method). This works directly on the time series rather than fitting the Allan deviation slope, making it more robust for mixed noise types. The ACF method is now the primary noise-ID in the pipeline; the legacy slope method is preserved as a cross-check.

### Study scope labels
Every `run_aisim_*()` function now returns a `study_scope_category` and `study_scope_description` in its result dictionary. Categories are:

- `FULLY_SIMULATED` — Rabi scan, Mach-Zehnder phase scan (all physics from AISim)
- `HYBRID_AISIM_PLUS_ANALYTICAL` — gravity sweep, vibration sweep (AISim for pulse transfer + analytical inertial phase)
- `ANALYTICAL_ONLY` — reserved for future pure-analytical studies

The HTML report renders a colour-coded panel (green for full, amber for hybrid) above each simulation block. This replaces the previous informal text convention with a machine-readable enum enforced by tests.

### Expanded published references
The reference registry grew from 4 to 12 entries. Two values were corrected: `freier_2016_sensitivity` (was 5e-8, should be 9.6e-8 m/s^2/sqrt(Hz)) and `menoret_2018_accuracy` (was mislabeled 2.5e-8, the real long-term stability is 1e-8 m/s^2). The old keys remain importable via deprecation shims emitting `DeprecationWarning`. New entries include Hu 2013, Peters 2001, Kasevich & Chu 1991, Bidel 2018 marine, and Peterson NLNM.
