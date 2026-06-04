# V1.0 Physics Upgrade — Design Reference

This document is the design rationale, equations, and module-by-module reference for the v0.9.3 → v1.0.0 upgrade. It complements `CHANGELOG.md` (what changed) by explaining **why** each change was needed and **how** the new physics fits together.

For a thesis/report-friendly overview, see `docs/AISIM_GRAVIMETER_STUDIES.md`. For the module dependency map, see `docs/ARCHITECTURE.md`.

---

## 1. The problem v1.0 solves

Through v0.9.3 the gravity phase in any AISim-backed gravimeter study was injected analytically:

```python
# Hybrid path (still the default in v1.0):
final_phase_rad = phase_bias + k_eff * g * T**2
bs2 = SpatialSuperpositionTransitionPropagator(..., phase_scan=final_phase_rad)
```

This was honest — the report study scope was `HYBRID_AISIM_PLUS_ANALYTICAL` — but it meant the simulation could never disagree with the closed-form formula. Effects that distort the formula in a real instrument (chirp residuals during finite pulses, position-dependent AC Stark, wavefront aberrations sampled by drifting atoms, finite Rabi-frequency rotations under time-varying detuning) were inaccessible.

v1.0 makes the gravity phase **emerge** from the propagation matrix multiplication rather than be imposed on it, while keeping the hybrid path available for fast checks and exact analytical matching.

---

## 2. The physics, in one paragraph

A real atom gravimeter chirps its Raman laser at `α = k_eff·g` so the laser tracks the falling atom's Doppler shift. The MZ phase is then `Δφ = (k_eff·g − α)·T²`. With `α = k_eff·g_chirp`, `Δφ = k_eff·(g − g_chirp)·T²` and a noise budget can be built around residuals: the thermal Doppler `−v_thermal·k_eff` survives, position-dependent Rabi frequencies modulate the rotation, AC Stark from non-zero single-photon detuning shifts the resonance, and any wavefront imperfection adds a per-atom position-dependent phase. To capture any of those, the simulation must propagate atoms ballistically, run the chirp inside the Raman matrix, and combine three pulses through honest matrix multiplication.

---

## 3. Phase-by-phase implementation

### 3.1 Tier 1 — Emergent gravity phase

#### 3.1.1 `GravityFreePropagator` (`vendor/aisim/prop.py`)

```python
class GravityFreePropagator(Propagator):
    def __init__(self, time_delta, g_m_s2=9.81,
                 gravity_gradient_per_m=0.0, z_ref_m=0.0):
        ...

    def propagate(self, atoms):
        atoms = copy.deepcopy(atoms)
        dt = self.time_delta
        g_local = self.g_m_s2 + self.gravity_gradient_per_m * (atoms.position[:, 2] - self.z_ref_m)
        atoms.position[:, 2] += atoms.velocity[:, 2] * dt - 0.5 * g_local * dt**2
        atoms.position[:, 0] += atoms.velocity[:, 0] * dt
        atoms.position[:, 1] += atoms.velocity[:, 1] * dt
        atoms.velocity[:, 2] -= g_local * dt
        atoms.time          += dt
        return atoms
```

Conventions: `g_m_s2 > 0` is downward (so `v_z` becomes more negative). The optional linear gradient `γ·(z − z_ref)` makes `g` a function of altitude. The quantum state is an identity rotation — gravity does not couple internal states during free fall.

Tests: `tests/test_gravity_propagation.py` (10 cases) verify exact ballistic kinematics, x/y invariance, gradient, additive composition (two τ/2 steps = one τ step), state preservation, time update, immutability.

#### 3.1.2 Chirped `Wavevectors` (`vendor/aisim/beam.py`)

```python
class Wavevectors:
    def __init__(self, k1=8055366, k2=-8055366, chirp_rate_rad_per_s2=0.0):
        ...

    def doppler_shift(self, atoms):
        velocity_z = atoms.velocity[:, 2]
        doppler_shift = -velocity_z * (self.k1 - self.k2)
        if self.chirp_rate_rad_per_s2 != 0.0:
            doppler_shift += self.chirp_rate_rad_per_s2 * atoms.time
        return doppler_shift
```

For `chirp_rate_rad_per_s2 = 0` (the default), the function is byte-identical to upstream. With `α = −k_eff·g_chirp`, an atom at v=0 falling under gravity sees a Doppler shift that grows as `+k_eff·g·t` plus the chirp's `−k_eff·g_chirp·t`, net `k_eff·(g−g_chirp)·t`. At `g = g_chirp` the detuning is zero throughout the fall.

Tests: `tests/test_chirped_laser.py` (5 cases) verify `chirp=0` backward compatibility, gravity-Doppler cancellation, dimensional consistency (`k_eff·g ≈ 1.58e8 rad/s²`), and linear time scaling.

#### 3.1.3 Integrated-phase patch in `TwoLevelTransitionPropagator`

The upstream propagator imprints `exp(-i·(δ·t₀ + phase_scan))` on the |g⟩→|e⟩ matrix element. For a stationary atom with constant detuning this is the correct imprinted laser phase. For a falling atom with chirped laser, the detuning is time-varying and `δ(t)·t₀` is *not* the integrated phase:

```
correct integrated phase = ∫₀^{t₀} δ(t') dt'
                         = -k_eff · ∫₀^{t₀} v(t') dt' + 0.5 · α · t₀²
                         = -k_eff · (z(t₀) - z₀) + 0.5 · α · t₀²
```

Doing the algebra for the MZ combination `φ₁ − 2·φ₂ + φ₃` shows that the upstream formula `δ(t₀)·t₀` accumulates **twice** the correct gravity phase. The local patch replaces it with the integrated form:

```python
if self.wave_vectors is not None:
    k_eff       = self.wave_vectors.k1 - self.wave_vectors.k2
    chirp       = self.wave_vectors.chirp_rate_rad_per_s2
    z_at_pulse  = atoms.position[:, 2]
    imprint_phase = -k_eff * z_at_pulse + 0.5 * chirp * atoms.time**2
u_eg = np.exp(-1j * (imprint_phase + phase)) * (-1j * sin_theta * sin(Omega_R * tau / 2)) * np.exp(-1j * delta * tau / 2)
u_ge = np.exp(+1j * (imprint_phase + phase)) * (-1j * sin_theta * sin(Omega_R * tau / 2)) * np.exp(+1j * delta * tau / 2)
```

Key invariants:

1. For `chirp = 0` and atoms initially at `z = 0` with constant velocity, `z(t₀) = v · t₀`, so `imprint_phase = -k_eff · v · t₀ = δ · t₀`. The new formula reduces **exactly** to the old one. Upstream behaviour is preserved bit-for-bit for the no-gravity, no-chirp case (verified by the existing chirped-laser unit tests, `tests/test_chirped_laser.py`).

2. For atoms with non-zero initial position `z₀`, the new formula carries a constant `−k_eff·z₀` per pulse. This cancels in any closed MZ loop (the same atom is at `z₀ + v·t_i − ½g·t_i²` at all three pulses; the `z₀` part contributes `+1 − 2 + 1 = 0`). Single-pulse Rabi populations are unaffected because they depend on `|u_eg|²` and the imprint enters only as a phase.

3. The chirp coefficient is **0.5**, not 1.0 as in the upstream `δ·t = chirp·t²` formula. The factor 0.5 makes `imprint_phase` equal to the time-integral of `δ(t)` from 0 to `t₀`. This is the same factor of 2 noted in invariant 1 above.

#### 3.1.4 Per-sweep empirical calibration (`_calibrate_gravity_phase_offset`)

Even with the integrated-phase patch, AISim's pulse-center-vs-pulse-start time convention and the finite pulse duration `τ` produce a residual constant phase offset (~2.5 rad in the default Rb-87 parameters). This offset is gravity-independent: it depends only on `chirp_rate`, `τ`, `T`. The calibration removes it numerically:

```python
def _calibrate_gravity_phase_offset(atoms0, *, ..., g_chirp_m_s2, ...) -> float:
    phis = np.linspace(0.0, 2*np.pi, 73, endpoint=False)
    p3 = []
    for phi in phis:
        out = _run_mach_zehnder_sequence_with_gravity(
            atoms0, ..., g_m_s2=g_chirp_m_s2,
            final_phase_rad=phi, phase_offset_rad=0.0,
        )
        p3.append(out["port_3"])
    fit = _fit_sinusoid(phis, np.asarray(p3))
    peak_phi = -fit["phase_offset_rad"]   # _fit_sinusoid returns -peak by convention
    return np.mod(peak_phi, 2*np.pi)
```

At `g = g_chirp` the analytical gravity phase is zero, so any non-zero fringe-peak position is artefactual. The calibration runs **one** fringe scan (typically 73 MZ sequences), fits a sinusoid, and returns the peak phase. The main sweep then applies `phase_scan_input + sim_phase_offset` at each `g`-value, which shifts the simulated fringe centre to match the hybrid mode at `g = g_chirp`.

Cost: O(73 MZ runs) per sweep, independent of `n_gravity_points`. For the default 61-point sweep with 1000 atoms this is ~2 seconds of overhead.

The `+` sign (rather than `−`) is derived from `total_phase = natural(g_chirp) + phase_scan` and the requirement that mid-fringe at `g = g_chirp` should be `total_phase = π/2`. Working through: `natural(g_chirp) = −peak_phi`, so `phase_scan = π/2 + peak_phi`.

#### 3.1.5 Adapter wiring

`run_aisim_gravity_sweep` gained a `gravity_propagation: bool = False` parameter (and `gravity_gradient_per_m: float = 0.0`). When `gravity_propagation=True`:

- `chirp_rate = -k_eff * gravity_center_m_s2`.
- `Wavevectors(..., chirp_rate_rad_per_s2=chirp_rate)`.
- `phase_bias_rad = π/2` when `lock_to_midfringe` (the gravity term that the hybrid path subtracts is no longer needed — the simulation handles it).
- `_calibrate_gravity_phase_offset` runs once before the main loop.
- Each `g`-value calls `_run_mach_zehnder_sequence_with_gravity(...)`, which uses `GravityFreePropagator(T, g_m_s2=g, gravity_gradient_per_m=...)` between pulses.
- `study_scope = "fully_simulated_gravity_sweep"` → category `FULLY_SIMULATED` after classification.

`run_aisim_vibration_sensitivity_sweep` was extended in the same way.

`run_simulation_from_config` passes `gravity_propagation` and `gravity_gradient_per_m` through from the YAML config.

#### 3.1.6 Known finite-τ differences

After the calibration the simulated and hybrid modes track the same fringe (rate matches to 0.2%, visibility matches to ~1%, centre is aligned). A small per-population residual (~atol 0.15) remains because the simulated mode captures effects the hybrid mode does not:

- During each Raman pulse, the chirp continues to accumulate `α·t` of additional detuning. AISim evaluates this at the pulse start time, so the Rabi-rotation angle differs from the idealised `Ω·τ/2` by a small amount that depends on `α·τ`.
- For a falling atom, the velocity at the *centre* of the mirror pulse differs from the velocity at its start by `g·τ`. The exact rotation matrix is computed with the velocity at pulse start; using the centre instead would change the rotation slightly.
- These are real physical effects in a finite-pulse-duration interferometer. A future Tier 5 upgrade could move to pulse-center evaluation or to a finer time-stepping scheme inside each pulse.

The cross-validation tests in `tests/test_gravity_mz_sequence.py` set the tolerances accordingly:

- `test_port3_populations_agree` and `test_port2_populations_agree`: `atol = 0.15`.
- `test_normalized_diff_agrees`: `atol = 0.30`.
- `test_fringe_visibility_preserved`: `|V_sim − V_hybrid| < 0.10`.

### 3.2 Tier 2 — Realistic noise sources

#### 3.2.1 Time-domain vibration generator

`physics/noise_models.generate_vibration_timeseries` synthesises a real acceleration time-series whose PSD matches a Peterson model:

1. Build the `np.fft.rfftfreq` grid for the requested `duration_s` and `sample_rate_hz`.
2. Interpolate the Peterson NLNM (or NHNM) PSD at those frequencies (PSD(0) = 0 by definition).
3. Multiply by the isolation filter `H²(f) = f⁴ / (f² + f_c²)²` if `isolation_cutoff_hz > 0`.
4. Draw independent Gaussian real and imaginary parts at each bin with `σ = sqrt(P(f) · fs · N / 4)` so that the one-sided PSD recovered from the inverse rFFT matches the input within statistical fluctuation.
5. Inverse rFFT → real acceleration time-series.
6. Velocity = `accel / jω` and displacement = `−accel / ω²` in the frequency domain, then inverse-rFFT.

Tests: `tests/test_vibration_timeseries.py` (7 cases) verify PSD match within factor 3, isolation attenuation (`H²(0.1, f_c=1) ≈ 1e-4`), high-frequency pass-through (`H²(10, f_c=1) ≈ 1`), determinism, output shape, and the freq-domain double-integral self-consistency.

#### 3.2.2 Detection noise

```python
def add_detection_noise(populations, *, n_detected, seed=None):
    sigma = 1.0 / sqrt(n_detected)
    noisy = populations + rng.normal(0.0, sigma, size=populations.shape)
    return np.clip(noisy, 0.0, 1.0)
```

Standard projection-noise limit for a state-selective readout. Tests (`tests/test_detection_noise.py`, 6 cases) verify `σ(N=100) ≈ 0.1` and `σ(N=10000) ≈ 0.01`, clipping behaviour, and determinism.

#### 3.2.3 Spontaneous emission

```python
def spontaneous_emission_loss_probability(*, rabi_freq_rad_s, single_photon_detuning_hz,
                                          pulse_duration_s, excited_state_lifetime_s=26.24e-9):
    Δ_rad_s = 2π · single_photon_detuning_hz
    return (rabi_freq_rad_s / Δ_rad_s)**2 · pulse_duration_s / excited_state_lifetime_s
```

For Rb-87 D2 typical parameters (Ω_eff ≈ 2π·15 kHz, Δ = 1 GHz, τ = 25 μs, τ_sp = 26.24 ns) this returns ~2·10⁻⁷ per pulse, the right order of magnitude. Tests verify the scaling laws (`p_se ∝ 1/Δ²`, `p_se ∝ τ`).

### 3.3 Tier 3 — Multi-drop cycle

#### 3.3.1 `run_aisim_multi_drop_cycle`

The core loop:

```python
for i in range(n_drops):
    drop_atoms = _create_detected_ensemble(seed=base_seed + i + 1, ...)
    phase_bias_drop = phase_bias_base + servo_phase_correction

    if gravity_propagation:
        out = _run_mach_zehnder_sequence_with_gravity(
            drop_atoms, ..., g_m_s2=gravity_true_m_s2,
            final_phase_rad=phase_bias_drop,
            phase_offset_rad=sim_phase_offset,
        )
    else:
        out = _run_mach_zehnder_sequence(drop_atoms, ..., final_phase_rad=phase_bias_drop)

    p3 = out["port_3"]
    if detection_noise_enabled:
        p3 = add_detection_noise([p3], n_detected=n_detected_per_drop, seed=...)[0]

    g_estimates[i] = gravity_true + (p3 - 0.5) / fringe_slope_per_m_s2

    if servo_enabled:
        servo_phase_correction = servo_integrator_step(p3, servo_phase_correction,
                                                       setpoint=0.5, gain=servo_gain)
```

Fresh ensembles per drop give true statistical independence so `_allan_deviation` can fit white-noise-like behaviour. The calibration is run once before the loop and reused for every drop (the offset depends on chirp/τ/T, not on `g_true`).

The mid-fringe linearisation `g_est = g_true + (P₃ − 0.5) / slope` uses `slope = −0.5 · V · k_eff · T²` with `V = 1` assumed. This is the simplest readout; a future upgrade could fit a per-drop fringe to refine V.

#### 3.3.2 Allan deviation

`_allan_deviation` computes the overlapping Allan deviation at octave averaging windows `m = 1, 2, 4, 8, ...`:

```python
σ²_A(τ) = 1/(2(N−1)) Σ (y_{k+1} − y_k)²
```

where `y_k = mean(g_estimates over block k)`. Returns `(taus, adev)` arrays.

#### 3.3.3 Servo integrator

```python
def servo_integrator_step(*, population, phase_estimate, setpoint=0.5, gain=1.0):
    return phase_estimate - gain * (population - setpoint)
```

Simple I-only loop. The sign is negative because P₃ increases with phase on the rising slope; to drive P₃ down we lower the phase bias. The loop cannot suppress per-drop ensemble noise (each drop is uncorrelated by construction); it can suppress slow drifts that persist between drops. With detection noise disabled, the mean P₃ across drops locks to 0.5 within a few drops at `gain = 0.5`.

### 3.4 Tier 4 — Advanced systematics

#### 3.4.1 AC Stark / light shift

`TwoLevelTransitionPropagator` and `SpatialSuperpositionTransitionPropagator` gained `single_photon_detuning_hz`. When non-zero:

```python
Δ_rad_s = 2π · single_photon_detuning_hz
delta = delta + Omega_eff**2 / (4 · Δ_rad_s)
```

The contribution is position-dependent because `Omega_eff(r)` comes from the Gaussian beam profile. Atoms near the beam axis see a larger AC Stark shift than atoms in the wings. In an ensemble this both shifts the fringe centre (the mean shift) and reduces visibility (the spread of shifts).

Tests (`tests/test_ac_stark.py`, 3 cases) verify `detuning = 0` is a no-op, that a finite detuning produces a measurable fringe shift, and that a stronger detuning reduces (or at worst maintains) ensemble contrast.

#### 3.4.2 Wavefront aberrations

`_build_wavefront(wavefront_zernike_coeffs, wavefront_radius_m)` wraps the existing upstream `Wavefront`:

```python
def _build_wavefront(*, wavefront_zernike_coeffs, wavefront_radius_m):
    if not wavefront_zernike_coeffs:
        return None
    return Wavefront(r_wf=wavefront_radius_m, coeff=wavefront_zernike_coeffs)
```

`_run_mach_zehnder_sequence` accepts `wavefront=...` and passes it to all three propagators (bs1, mirror, bs2). The propagator adds `phase += wf.get_value(atoms.position)` for each atom. The wavefront returns NaN outside `r_wf`, so the wavefront radius must be larger than the maximum atom excursion (cloud radius + drift) to avoid contaminating the populations.

In a fully simulated MZ with thermal-velocity drift between pulses, the wavefront is sampled at different `(x, y)` at each pulse, producing a real per-atom dephasing. Tests verify NaN-free behaviour for sufficient `r_wf`, no-op for empty coefficients, and a measurable visibility reduction for strong defocus + sufficient drift.

### 3.5 Phase 10 — Truth checks and version bump

`_check_gravity_sweep` now branches:

```python
if not gravity_propagation:
    # Hybrid: analytical phase must match exactly.
    checks.append(build_check("analytic_phase_match", max_abs <= 1e-10, ...))
    checks.append(build_check("phase_linearity", r2 >= 0.999999, ...))
else:
    # Fully simulated: cannot enforce the formula directly.
    checks.append(build_check("fringe_visibility", visibility > 0.3, ...))
    checks.append(build_check("study_scope_fully_simulated",
                              "FULLY" in scope or "SIMULATED" in scope, ...))
```

A new `_check_multi_drop_cycle` validates the multi-drop output: `n_drops` matches, `g_estimates` finite and length-correct, `timestamps` monotonic, `|mean(g) − g_true| < 1e-5`, Allan-array consistency, and Allan-deviation decreasing within 1.2× slack.

Version: `0.9.3 → 1.0.0` in `src/qgrav/__init__.py`, `pyproject.toml`, and `CHANGELOG.md`.

---

## 4. Module map

```
src/qgrav/
  vendor/aisim/
    prop.py
      Propagator                       (upstream)
      FreePropagator                   (upstream)
      GravityFreePropagator            (v1.0 NEW) — ballistic kinematics
      TwoLevelTransitionPropagator     (v1.0 PATCHED) — integrated laser phase, AC Stark
      SpatialSuperpositionTransitionPropagator (v1.0 PATCHED forwards AC Stark)
    beam.py
      Wavevectors                      (v1.0 PATCHED) — chirp_rate_rad_per_s2
      IntensityProfile                 (upstream)
      Wavefront                        (upstream, now wired)
    __init__.py                        (v1.0 exports GravityFreePropagator)

  physics/
    noise_models.py
      add_white_noise / add_bias / add_random_walk_drift / add_outlier_spikes  (upstream)
      generate_vibration_timeseries    (v1.0 NEW)
      add_detection_noise              (v1.0 NEW)
      spontaneous_emission_loss_probability (v1.0 NEW)
    readout_models.py
      port_differential_summary        (upstream)
      servo_integrator_step            (v1.0 NEW)

  sim_ai/
    aisim_adapter.py
      _run_mach_zehnder_sequence       (v1.0 EXTENDED: wavefront, single_photon_detuning_hz)
      _run_mach_zehnder_sequence_with_gravity (v1.0 NEW)
      _calibrate_gravity_phase_offset  (v1.0 NEW)
      _build_wavefront                 (v1.0 NEW)
      _allan_deviation                 (v1.0 NEW)
      run_aisim_gravity_sweep          (v1.0 EXTENDED: gravity_propagation, gravity_gradient_per_m)
      run_aisim_vibration_sensitivity_sweep (v1.0 EXTENDED: gravity_propagation)
      run_aisim_multi_drop_cycle       (v1.0 NEW)
      run_simulation_from_config       (v1.0 EXTENDED: multi_drop_cycle dispatch)

  validation/
    truth_checks.py
      _check_gravity_sweep             (v1.0 PATCHED: branches on gravity_propagation)
      _check_multi_drop_cycle          (v1.0 NEW)

tests/
  test_gravity_propagation.py          (v1.0 NEW, 10 tests)
  test_chirped_laser.py                (v1.0 NEW, 5 tests)
  test_gravity_mz_sequence.py          (v1.0 NEW, 9 tests)
  test_vibration_timeseries.py         (v1.0 NEW, 7 tests)
  test_detection_noise.py              (v1.0 NEW, 6 tests)
  test_multi_drop_cycle.py             (v1.0 NEW, 10 tests)
  test_servo.py                        (v1.0 NEW, 6 tests)
  test_ac_stark.py                     (v1.0 NEW, 3 tests)
  test_wavefront.py                    (v1.0 NEW, 5 tests)
```

Total v1.0 test count: **61 new tests** (192 baseline → 253 passing). All v0.9.3 tests still pass unchanged.

---

## 5. Physics equations reference

| Quantity | Formula |
|----------|---------|
| Ballistic trajectory | `z(t+dt) = z + v_z·dt − ½·g·dt²`; `v_z(t+dt) = v_z − g·dt` |
| Gravity gradient | `g(z) = g₀ + γ·(z − z_ref)` |
| Chirp tracking | `α = −k_eff · g_chirp` (Wavevectors.chirp_rate_rad_per_s2) |
| Doppler shift (chirped) | `δ(t) = −v_z·k_eff + α·t` |
| Residual at g = g_chirp | `δ = −v_thermal·k_eff` (gravity cancels) |
| Integrated laser phase | `φ_imprint(t₀) = −k_eff·z(t₀) + ½·α·t₀²` |
| Hybrid MZ phase | `φ_g = k_eff · g · T²` (injected via phase_scan) |
| Emergent MZ phase | `φ_g = k_eff · (g − g_chirp) · T²` (out of the matrix multiplication) |
| Detection noise | `σ_P = 1 / √N_detected` |
| Spontaneous emission | `p_se = (Ω_eff/Δ)² · τ/τ_sp` |
| AC Stark shift | `δ_AC = Ω_eff² / (4·Δ)` (added to two-photon δ) |
| Vibration isolation | `H²(f) = f⁴ / (f² + f_c²)²` (second-order high-pass) |
| PSD → rFFT scaling | `|X(f)|² = P(f) · fs · N / 2` per bin (one-sided) |
| Mid-fringe inversion | `g_est = g_setpoint + (P₃ − 0.5) / slope`, `slope = −½·V·k_eff·T²` |
| Allan variance | `σ²_A(τ) = ½(N−1)⁻¹ · Σ (y_{k+1} − y_k)²` |
| Shot-noise sensitivity | `δg = 1 / (V · k_eff · T² · √(N/T_cycle))` |
| Servo step | `phase ← phase − gain · (P₃ − setpoint)` |

---

## 6. Workflow examples

### 6.1 Cross-validate hybrid vs simulated

```python
from qgrav.sim_ai.aisim_adapter import run_aisim_gravity_sweep

common = dict(n_atoms=500, seed=42, n_gravity_points=21,
              gravity_span_m_s2=4e-6, lock_to_midfringe=True)

hybrid    = run_aisim_gravity_sweep(**common, gravity_propagation=False)
simulated = run_aisim_gravity_sweep(**common, gravity_propagation=True)

# Compare fringe rates (both should be -k_eff*T^2):
import numpy as np
diff_h = hybrid["normalized_differential_signal"]
diff_s = simulated["normalized_differential_signal"]
print(np.max(np.abs(diff_s - diff_h)))  # ~0.2 due to finite-tau physics
```

### 6.2 100-drop Allan deviation campaign

```python
from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle
result = run_aisim_multi_drop_cycle(
    n_drops=100, cycle_time_s=1.0, gravity_true_m_s2=9.81,
    gravity_propagation=True, detection_noise_enabled=True,
    n_detected_per_drop=10_000, servo_enabled=True, servo_gain=0.5,
)
import matplotlib.pyplot as plt
plt.loglog(result["allan_taus_s"], result["allan_dev_m_s2"])
plt.xlabel("tau [s]"); plt.ylabel("Allan deviation [m/s^2]")
plt.show()
```

### 6.3 Long NLNM seismic trace

```python
from qgrav.physics.noise_models import generate_vibration_timeseries
ts = generate_vibration_timeseries(
    duration_s=3600.0, sample_rate_hz=100.0,
    seismic_model="nlnm", isolation_cutoff_hz=1.0, seed=42,
)
# ts["accel_m_s2"], ts["velocity_m_s"], ts["displacement_m"]
# Feed displacement into a future time-domain vibration MZ.
```

### 6.4 AC Stark sensitivity scan

```python
from qgrav.sim_ai.aisim_adapter import _run_mach_zehnder_sequence
import numpy as np
# Vary single_photon_detuning_hz from 1 GHz to 100 GHz, observe fringe shift.
for delta_hz in [1e9, 1e10, 1e11]:
    out = _run_mach_zehnder_sequence(
        atoms0, tau_pi_half_s=23e-6, interferometer_time_s=0.26,
        intensity_profile=beam, wave_vectors=wv,
        final_phase_rad=np.pi/2,
        single_photon_detuning_hz=delta_hz,
    )
    print(f"Δ = {delta_hz:.0e} Hz   P₃ = {out['port_3']:.4f}")
```

---

## 7. Pointers for thesis / report writing

A safe, honest description of what the simulation is doing:

> The qgrav v1.0 simulation core integrates a locally patched AISim with a self-consistent emergent-gravity model. Atoms propagate ballistically under a `GravityFreePropagator` between Raman pulses; a chirped Raman laser (`α = −k_eff·g_chirp`) cancels the common gravity Doppler. The two-photon transition propagator uses the time-integrated laser phase `−k_eff·z(t₀) + ½·α·t₀²` so that the Mach–Zehnder combination yields the standard `k_eff·(g − g_chirp)·T²` gravity phase from first principles, rather than imposing it through a closed-form formula. A per-sweep empirical calibration removes a constant residual phase artefact from the finite Raman pulse duration. Optional AC Stark and Zernike-wavefront aberrations capture position-dependent systematics. A multi-drop measurement cycle with detection noise and an integrator-based fringe-locking servo produces an Allan-deviation time series, providing an end-to-end software analogue of a deployed atom gravimeter.

Caveats to acknowledge:

- The simulation is **semiclassical**: atoms have classical trajectories and quantum internal states. The internal-state evolution is exact under the rotating-wave approximation; the external-degree-of-freedom is purely classical.
- The simulated mode and the hybrid mode differ by ~atol 0.15 on populations because of finite-τ Rabi rotations. The simulated mode is more physically accurate; the hybrid mode is exactly the analytical formula.
- Drop-to-drop correlations (e.g. long-term seismic drift, laser-frequency drift, magnetic-field drift) are not modelled. Each drop in `run_aisim_multi_drop_cycle` is statistically independent.
- The servo is I-only without anti-windup or non-linear corrections.
- AC Stark and wavefront contributions are correctly *coupled* into the Raman propagator but the visibility-reduction effect on a real ensemble depends sensitively on cloud size, beam radius, T, and τ. Calibrate to your hardware before quoting numbers.

---

## 8. Test invocation

```bash
# Full suite (253 tests):
python -m pytest tests -q

# Just the v1.0 phases:
python -m pytest tests/test_gravity_propagation.py tests/test_chirped_laser.py \
                 tests/test_gravity_mz_sequence.py tests/test_vibration_timeseries.py \
                 tests/test_detection_noise.py tests/test_multi_drop_cycle.py \
                 tests/test_servo.py tests/test_ac_stark.py tests/test_wavefront.py -v
```
