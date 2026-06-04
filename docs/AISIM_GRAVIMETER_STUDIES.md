# AISim gravimeter studies

This document explains the AISim simulation studies in qgrav, what they mean scientifically, and what they do **not** claim.

> **v1.0 update:** the `gravity_sweep` and `vibration_sensitivity_sweep` studies now have a **fully simulated** mode (`gravity_propagation: true`) in which the gravity phase emerges from a ballistic atom trajectory under a chirped Raman laser. A new **`multi_drop_cycle`** model simulates a full N-drop gravimeter measurement cycle. See section 6 below.

## 1. Why these studies exist

The project now has three complementary lanes:

1. **Signal-processing lane**
   - virtual interferometer I/Q data
   - baseline vs improved estimators
   - PSD / Allan deviation / reports

2. **Real-data gravimetry lane**
   - superconducting gravimeter residual data
   - gap checks, PSD, Allan deviation, long-term drift/stability summaries

3. **AISim gravimeter-study lane**
   - atom-optics simulation studies that are closer to light-pulse gravimeter physics

This AISim stage moves the project from a generic atom-light demo toward a gravimeter-relevant software study.

---

## 2. The three studies in this stage

### 2.1 Mach–Zehnder phase scan

Config example:
- `configs/example_aisim_phase_scan.yaml`

Model name:
- `mach_zehnder_phase_scan`

What is simulated directly in AISim:
- a **three-pulse** sequence using `SpatialSuperpositionTransitionPropagator`
- first beam splitter pulse
- free evolution for time `T`
- mirror pulse
- free evolution for time `T`
- final beam splitter pulse with a configurable `phase_scan`

What is reported:
- output-port populations (`port 2`, `port 3`)
- differential signal
- fitted fringe visibility
- fitted phase offset
- a fit quality score (R²)

Why it matters:
- this is the closest study in the repo to a real light-pulse atom interferometer fringe measurement
- it shows whether the selected pulse/ensemble settings produce a usable interferometer signal

What it does **not** claim:
- it is still a compact study, not a full field gravimeter digital twin
- it does not include every systematic effect of a deployed absolute gravimeter

---

### 2.2 Gravity sweep

Config example:
- `configs/example_aisim_gravity_sweep.yaml`

Model name:
- `gravity_sweep`

What it does:
- keeps the AISim three-pulse sequence for pulse-transfer/contrast behavior
- maps gravity `g` to interferometer phase using the standard Mach–Zehnder scaling

In other words, this is a **hybrid study**:
- pulse sequence + imperfect populations: **AISim**
- gravity-induced phase law: **analytical gravimeter model**

Why this hybrid is used:
- it is honest and practical
- it gives a gravimeter-relevant sweep now, without pretending AISim alone already includes every deployed-gravimeter effect end-to-end in this repo

What is reported:
- gravity values
- total phase used for each gravity point
- output-port populations
- differential / normalized differential signal
- mid-fringe slope near the operating point

What it means:
- this shows how sensitive the simulated interferometer output is to small gravity changes

---

### 2.3 Vibration sensitivity sweep

Config example:
- `configs/example_aisim_vibration_sweep.yaml`

Model name:
- `vibration_sensitivity_sweep`

What it does:
- uses the same hybrid gravimeter idea
- adds a sinusoidal reference-mirror motion model
- converts that mirror motion into interferometer phase using the three-pulse discrete phase response

The phase model used is the standard pulse-time approximation:
- pulse times at `0`, `T`, `2T`
- vibration phase from the mirror positions at those pulse times

What is reported:
- vibration amplitude sweep
- induced vibration phase
- equivalent gravity error
- output-port populations and differential signal

Why it matters:
- vibration is one of the most important practical limitations in real atom gravimeters
- this gives you a software-only way to study vibration sensitivity before any hardware exists

What it does **not** claim:
- it is not a full seismic/isolation model
- it is a clean first-order sensitivity study

---

## 3. How to interpret the study types

### `full_aisim_three_pulse_sequence`
This means the three-pulse interferometer sequence itself is simulated directly with AISim.

### `hybrid_aisim_plus_analytic_gravity_phase`
This means:
- AISim handles the pulse-transfer / atom-optics part
- the gravity phase is imposed analytically using the standard Mach–Zehnder gravimeter scaling

### `hybrid_aisim_plus_analytic_vibration_phase`
This means:
- AISim handles the pulse-transfer / atom-optics part
- the vibration phase is imposed analytically from the mirror-motion phase response of a three-pulse interferometer

These labels are intentionally explicit so the report stays scientifically honest.

---

## 4. Recommended thesis/report wording

A safe and accurate way to describe this stage is:

> The project integrates AISim into a software-first gravimeter R&D platform and implements three gravimeter-relevant studies: a full three-pulse Mach–Zehnder phase scan in AISim, a hybrid gravity sweep combining AISim pulse-transfer effects with the standard light-pulse gravimeter phase law, and a hybrid vibration sensitivity sweep using the discrete three-pulse vibration phase response.

A shorter version is:

> The simulation layer now goes beyond Rabi oscillations and includes gravimeter-relevant phase, gravity, and vibration studies.

---

## 5. What should come next after this stage

The best next upgrades are:

1. add **run comparison** across the three AISim studies
2. add **frequency sweeps** for vibration sensitivity, not just amplitude sweeps
3. add **wavefront / beam-size / temperature sensitivity** sweeps using AISim inputs
4. compare synthetic stability summaries against the real gravimetry data lane

That is the path from a strong thesis-quality project toward a more publishable methodology study.

---

## 6. v1.0 — Fully simulated and multi-drop studies

The v0.x version of this document above describes a **hybrid** gravity sweep in which AISim handles the pulse-transfer / atom-optics part and the gravity phase is imposed analytically through `k_eff * g * T^2`. In **v1.0** that limitation has been removed. The same model name (`gravity_sweep`) can now be run in either mode:

```yaml
simulation:
  enabled: true
  backend: aisim
  model: gravity_sweep
  gravity_propagation: false   # default = hybrid (original behaviour)
```

vs

```yaml
simulation:
  enabled: true
  backend: aisim
  model: gravity_sweep
  gravity_propagation: true    # v1.0 = gravity phase emerges from the simulation
```

### 6.1 Gravity sweep, fully simulated (`gravity_propagation: true`)

What is simulated directly:

- A **three-pulse** sequence using `SpatialSuperpositionTransitionPropagator` (same as the hybrid path).
- Between pulses, atoms are propagated by a new **`GravityFreePropagator`** that performs exact ballistic kinematics under uniform `g`: `z(t+dt) = z + v_z·dt − ½·g·dt²`, `v_z(t+dt) = v_z − g·dt`. An optional linear gravity gradient `γ·(z − z_ref)` is supported.
- The Raman laser is **frequency-chirped** at `α = −k_eff · gravity_center_m_s2` so that, for an atom co-falling with the central gravity value, the velocity-induced Doppler shift cancels (`δ = −v_z·k_eff + α·t ≈ 0`).
- The locally patched `TwoLevelTransitionPropagator` uses the **physically correct integrated laser phase** `φ_imprint(t₀) = −k_eff·z(t₀) + ½·α·t₀²` instead of the upstream `δ·t₀` (which double-counts gravity and chirp phases when the detuning is time-varying).

What is reported (same keys as the hybrid path):

- gravity values, output-port populations, differential / normalized differential signal, mid-fringe slope.

What is different:

- `study_scope_category` is now `FULLY_SIMULATED` (green panel in the report).
- `truth_checks` no longer asserts an exact match to the analytical phase formula; instead it asserts that the fringe has reasonable visibility (`> 0.3`) and that the scope was correctly classified.
- A small **per-sweep empirical calibration** (`_calibrate_gravity_phase_offset`) removes a residual pulse-timing offset by running one extra fringe scan at `g = gravity_center_m_s2`. The cost is O(1) per sweep.
- Cross-validation tests verify that the simulated fringe matches the hybrid fringe within atol = 0.15 on populations and atol = 0.30 on the normalized differential signal. The remaining mismatch is a real physical difference: finite Raman pulse durations introduce τ-dependent residual detunings during pulses that the analytical formula ignores. The simulated mode captures this; the hybrid mode does not.

### 6.2 Vibration sensitivity sweep, fully simulated (`gravity_propagation: true`)

Same logic as above: the AISim pulse sequence is run with `GravityFreePropagator` and a chirped `Wavevectors`. The sinusoidal mirror motion is still added analytically as a phase scan on the final beamsplitter (a future upgrade could replace this with a real mirror-displacement model fed from `generate_vibration_timeseries`).

### 6.3 Multi-drop measurement cycle (`multi_drop_cycle`)

This is a new study model, configured by

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

What it simulates:

- N independent drops at a 1/T_cycle cadence.
- Each drop creates a **fresh** atom ensemble (`seed = base_seed + i + 1`) so the per-drop ensemble noise is genuinely uncorrelated.
- Each drop runs a full three-pulse Mach–Zehnder sequence (in either fully simulated or hybrid mode).
- Detection (projection) noise with σ = 1/√N_detected is added to each port population.
- An optional digital integrator **servo** adjusts the phase bias between drops to keep `P₃ ≈ 0.5` (mid-fringe).
- A linear mid-fringe inversion converts each `P₃` into a gravity estimate `g_est = g_setpoint + (P₃ − 0.5) / fringe_slope`.

What is reported:

- `g_estimates_m_s2` — one estimate per drop.
- `timestamps_s` — equispaced at `cycle_time_s`.
- `mean_g_m_s2`, `std_g_m_s2`, `mean_minus_true_m_s2`.
- `allan_taus_s`, `allan_dev_m_s2` — overlapping Allan deviation across octave averaging windows.
- `port_3_raw`, `port_3_noisy` — diagnostics for the readout chain.
- `study_scope_category` = `FULLY_SIMULATED` when `gravity_propagation: true`.

Why it matters:

- This is the closest the platform comes to simulating a full gravimeter measurement campaign.
- Allan deviation is the standard sensitivity figure of merit for atom gravimeters; here it can now be computed end-to-end from a microscopic ensemble simulation, with realistic detection noise and (optionally) a closed-loop servo.
- The servo demonstrates that an integrator loop can lock the operating point and that the resulting g-estimate trajectory is unbiased (truth check: `|mean(g) − g_true| < 1e-5`).

What it does **not** yet do:

- Drop-to-drop correlations (e.g. seismic drift) are not modelled. Each drop is independent.
- The servo is a simple integrator without anti-windup or non-linear corrections.
- Visibility is assumed unity for the P₃ → g inversion; a calibration scan could refine this.

### 6.4 Time-domain vibration noise (`generate_vibration_timeseries`)

Not a top-level study model — a building block. Given a duration, sample rate, and Peterson model name (NLNM or NHNM), this generator produces a realistic acceleration time-series whose PSD matches the chosen model, with an optional second-order high-pass isolation filter `H²(f) = f⁴/(f² + f_c²)²`. Velocity and displacement time-series are derived by frequency-domain integration.

The intended use is to feed long acceleration/displacement traces into a future "real-mirror" vibration MZ that consumes `z(0), z(T), z(2T)` from the time-series instead of an analytical sinusoid. A `vibration_model="time_domain"` switch on the vibration sweep is left for a follow-up release.

### 6.5 AC Stark / light shift (`single_photon_detuning_hz`)

`TwoLevelTransitionPropagator` and `SpatialSuperpositionTransitionPropagator` accept an optional `single_photon_detuning_hz`. When non-zero, the two-photon Raman detuning gains the AC Stark contribution `Ω_eff² / (4·Δ)`, where Ω_eff is the position-dependent effective Rabi frequency from the Gaussian beam profile and `Δ = 2π·single_photon_detuning_hz`. This is wired into `_run_mach_zehnder_sequence` so any AISim study can be re-run with light-shift effects enabled.

### 6.6 Wavefront aberrations (`_build_wavefront`)

`_build_wavefront(wavefront_zernike_coeffs, wavefront_radius_m)` constructs an AISim `Wavefront` from a dictionary of Zernike coefficients (Wyant ordering by default). When passed to `_run_mach_zehnder_sequence`, the wavefront imprints a position-dependent phase on each of the three pulses; thermal-velocity-driven drift between pulses makes the wavefront contribution per-atom-non-cancelling, which **reduces** ensemble visibility and shifts the operating point.

---

## 7. Recommended thesis/report wording (v1.0)

A safe and accurate way to describe the v1.0 simulation layer:

> qgrav's simulation core integrates a locally patched AISim with a self-consistent emergent-gravity model. Atoms propagate under a `GravityFreePropagator` between Raman pulses; a chirped Raman laser cancels the common gravity Doppler. The propagator's matrix elements use the time-integrated laser phase `−k_eff·z(t₀) + ½·α·t₀²` so that the Mach–Zehnder combination yields the standard `k_eff·(g − g_chirp)·T²` gravity phase from first principles, rather than imposing it through a closed-form formula. A multi-drop measurement cycle with detection noise and an optional fringe-locking servo produces an Allan-deviation time series, providing an end-to-end software analogue of a deployed atom gravimeter.

A shorter version:

> The simulation layer now derives the gravity phase from a ballistic atom trajectory under a chirped Raman laser, rather than injecting it analytically, and includes a multi-drop measurement-cycle simulator with realistic detection noise and Allan-deviation analysis.
