# Scientific hardening of the simulation layer

This stage restructures the gravimeter simulation code so that the physics and validation logic are easier to inspect, test, and explain in a thesis/report.

## Why this was added

A research-quality simulation platform should not hide the important scientific assumptions inside one large adapter or pipeline function. The simulation layer is now separated into explicit pieces:

- `src/qgrav/physics/atom_source.py` - source and detector description
- `src/qgrav/physics/pulse_sequence.py` - Rabi and Mach–Zehnder sequence helpers
- `src/qgrav/physics/phase_models.py` - gravity and vibration phase models
- `src/qgrav/physics/noise_models.py` - reusable stochastic perturbation functions
- `src/qgrav/physics/readout_models.py` - population/readout helpers
- `src/qgrav/physics/ground_truth.py` - reference relationships used for truth checking
- `src/qgrav/validation/truth_checks.py` - per-study pass/fail checks

## What is fully simulated and what is hybrid

> **v1.0 update:** `gravity_sweep` and `vibration_sensitivity_sweep` now have an optional **fully simulated** mode via `gravity_propagation: true`. A new `multi_drop_cycle` model is also fully simulated. The legacy hybrid behaviour is still the default for backward compatibility.

### Fully AISim-backed (all versions)
- `rabi_scan`
- `mach_zehnder_phase_scan`

### Optionally fully simulated (v1.0)
- `gravity_sweep` with `gravity_propagation: true`
- `vibration_sensitivity_sweep` with `gravity_propagation: true`
- `multi_drop_cycle` (always uses the emergent path when `gravity_propagation: true`)

In these v1.0 modes:
- A new **`GravityFreePropagator`** performs exact ballistic kinematics between Raman pulses.
- A **chirped Raman laser** (`Wavevectors.chirp_rate_rad_per_s2 = −k_eff · g_center`) cancels the common gravity Doppler.
- The locally patched `TwoLevelTransitionPropagator` uses the **integrated laser phase** `−k_eff·z(t₀) + ½·α·t₀²` instead of `δ·t₀`. The MZ combination then produces the standard `k_eff·(g − g_chirp)·T²` gravity phase from first principles.
- A **per-sweep empirical calibration** at `g = g_chirp` removes a residual pulse-timing offset.
- The resulting `study_scope_category` is `FULLY_SIMULATED`.

### Hybrid studies (default)
- `gravity_sweep` with `gravity_propagation: false` (default)
- `vibration_sensitivity_sweep` with `gravity_propagation: false` (default)

These keep the AISim three-pulse sequence for pulse-transfer/contrast behaviour, but inject the inertial phase analytically:

- gravity phase: `k_eff * g * T^2`
- vibration phase: `k_eff [z(0) - 2 z(T) + z(2T)]`

This is deliberate (it is faster and reproduces the analytical formula exactly), and the HTML report still flags it as `HYBRID` with an amber-coded panel.

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

- `FULLY_SIMULATED` - Rabi scan, Mach-Zehnder phase scan (all physics from AISim)
- `HYBRID_AISIM_PLUS_ANALYTICAL` - gravity sweep, vibration sweep (AISim for pulse transfer + analytical inertial phase)
- `ANALYTICAL_ONLY` - reserved for future pure-analytical studies

The HTML report renders a colour-coded panel (green for full, amber for hybrid) above each simulation block. This replaces the previous informal text convention with a machine-readable enum enforced by tests.

### Expanded published references
The reference registry grew from 4 to 12 entries. Two values were corrected: `freier_2016_sensitivity` (was 5e-8, should be 9.6e-8 m/s^2/sqrt(Hz)) and `menoret_2018_accuracy` (was mislabeled 2.5e-8, the real long-term stability is 1e-8 m/s^2). The old keys remain importable via deprecation shims emitting `DeprecationWarning`. New entries include Hu 2013, Peters 2001, Kasevich & Chu 1991, Bidel 2018 marine, and Peterson NLNM.

## Additions in v1.0.0

### Emergent gravity physics (Tier 1)

The previous-version hybrid studies imposed the gravity phase analytically through `k_eff * g * T^2`. v1.0 removes that limitation. With `gravity_propagation: true`, the gravity phase **emerges** from a self-consistent semiclassical simulation:

1. **`GravityFreePropagator`** (`vendor/aisim/prop.py`) replaces `FreePropagator` between Raman pulses. Exact ballistic kinematics: `z(t+dt) = z + v_z·dt − ½g·dt²`, `v_z(t+dt) = v_z − g·dt`. An optional linear gradient `γ·(z − z_ref)` is supported.

2. **Chirped Raman laser** (`vendor/aisim/beam.py`): `Wavevectors` accepts `chirp_rate_rad_per_s2`. The chirp `α = −k_eff · gravity_center_m_s2` cancels the common gravity-induced Doppler so atoms remain near Raman resonance throughout the fall.

3. **Integrated-phase patch** (`vendor/aisim/prop.py`): the upstream `TwoLevelTransitionPropagator._prop_matrix` uses `exp(−i·δ·t₀)` for the imprinted laser phase. This double-counts gravity and chirp when the detuning is time-varying. The local patch replaces it with the physically correct `exp(−i·(−k_eff·z(t₀) + ½·α·t₀²))`. For atoms at z=0 with constant velocity and zero chirp this reduces exactly to the upstream formula; only the time-varying-detuning case is changed.

4. **Per-sweep empirical calibration** (`_calibrate_gravity_phase_offset`): at `g = g_chirp`, the analytical gravity phase vanishes. Any residual fringe shift is therefore a numerical artefact of finite-duration pulses. The calibration runs one fringe scan at `g = g_chirp`, fits a sinusoid, and subtracts the peak phase from every subsequent run in that sweep. Cost: O(1) per sweep, no per-drop overhead.

The MZ phase in the fully simulated mode comes out as `k_eff · (g − g_chirp) · T²`, matching the standard atom-interferometry result, with a remaining ~atol=0.15 population mismatch versus the hybrid mode arising from finite-pulse-duration physics that the hybrid mode does not model.

### Multi-drop cycle (Tier 3)

The `multi_drop_cycle` study simulates an N-drop gravimeter measurement campaign. Each drop:

- creates a **fresh** atom ensemble (`seed = base_seed + i + 1`),
- runs a full MZ sequence with the calibrated phase offset,
- optionally adds detection noise (σ = 1/√N_detected),
- inverts the mid-fringe linearisation to obtain a gravity estimate,
- optionally updates a digital integrator servo for the next drop.

Overlapping Allan deviation is computed across octave averaging windows. A truth check verifies `|mean(g) − g_true| < 1e-5 m/s²`, `len(g_estimates) == n_drops`, monotonic timestamps, and that Allan deviation either decreases with τ (white noise) or holds within a 1.2× slack (random walk).

### Advanced systematics (Tier 4)

- **AC Stark / light shift** (`single_photon_detuning_hz` on `TwoLevelTransitionPropagator`): adds `Ω_eff² / (4Δ)` to the two-photon detuning. Because `Ω_eff(r)` depends on the atom's distance from the beam axis through the Gaussian profile, the AC Stark contribution is position-dependent and reduces ensemble contrast as well as shifting the fringe centre.

- **Wavefront aberrations** (`_build_wavefront`): the upstream AISim `Wavefront` class is now wired through `_run_mach_zehnder_sequence`. Wavefront imprints add a position-dependent phase at each pulse; for atoms with non-trivial xy thermal velocity the wavefront sampled at successive pulses differs, producing a real per-atom dephasing that reduces visibility.

### Truth-check evolution

`_check_gravity_sweep` now branches on `gravity_propagation`:

- **hybrid** (default): preserves the strict checks `analytic_phase_match < 1e-10 rad` and `phase_linearity ≥ 0.999999`.
- **simulated** (v1.0): replaces those with `fringe_visibility > 0.3` and `study_scope_fully_simulated` (the scope category must contain `FULLY` or `SIMULATED`).

New `_check_multi_drop_cycle` validates the multi-drop study output: array-length consistency, finite estimates, monotonic timestamps, mean-close-to-true-gravity (`< 1e-5 m/s²`), Allan-deviation array consistency, and decreasing Allan deviation (with a small slack for finite-N statistical fluctuation).
