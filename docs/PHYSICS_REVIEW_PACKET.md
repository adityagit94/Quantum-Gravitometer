# Physics Review Packet - qgrav v1.0 AISim Patches

**Document version**: 1.0
**Code version**: qgrav 1.0.0
**For review by**: an atom-interferometry researcher (PhD student, postdoc, or PI with hands-on light-pulse atom-gravimeter experience)
**Estimated read time**: 60–90 minutes
**Estimated review time** (skim + targeted answer of §11 questions): 1.5–2 hours

---

## Table of contents

1. [What this document is and is not](#1-what-this-document-is-and-is-not)
2. [Quick-start reference frame](#2-quick-start-reference-frame)
3. [The upstream AISim model](#3-the-upstream-aisim-model)
4. [The problem with `δ·t₀` for time-varying detuning](#4-the-problem-with-δt-for-time-varying-detuning)
5. [Patch A - `GravityFreePropagator` (new class)](#5-patch-a--gravityfreepropagator-new-class)
6. [Patch B - chirped `Wavevectors`](#6-patch-b--chirped-wavevectors)
7. [Patch C - integrated laser phase in `TwoLevelTransitionPropagator`](#7-patch-c--integrated-laser-phase-in-twoleveltransitionpropagator)
8. [The empirical calibration step](#8-the-empirical-calibration-step)
9. [Cross-validation results](#9-cross-validation-results)
10. [Known finite-τ residuals](#10-known-finite-τ-residuals)
11. [Reviewer questions (the asks)](#11-reviewer-questions-the-asks)
12. [Executable notebook stub](#12-executable-notebook-stub)
13. [References](#13-references)
14. [Glossary and conventions](#14-glossary-and-conventions)

---

## 1. What this document is and is not

### What this is

A self-contained physics review packet for three patches we made to a vendored copy of the open-source `aisim` atom-interferometry simulator (AISim v0.4-ish), in service of building a fully-simulated atom gravimeter where the gravity phase emerges from the simulation rather than being injected as `k_eff·g·T²`.

We are asking an external expert to verify that:

- The new `GravityFreePropagator` is correct (it is straight ballistic kinematics, but worth checking for sign conventions and gradient handling).
- The chirped `Wavevectors` does what it claims (cancels gravity-induced Doppler in the rotating frame of the laser).
- The integrated laser phase formula `−k_eff·z(t₀) + ½·α·t₀²` is the physically correct replacement for the upstream `δ·t₀` factor in the `u_eg` / `u_ge` matrix elements.
- The empirical per-sweep calibration step we use to remove a residual ~2.5 rad constant phase offset is interpretable (i.e., what is the physical origin of the offset, and is removing it via calibration legitimate or hiding a bug?).
- The cross-validation tolerance between the hybrid and simulated modes (`atol = 0.15` on populations, `atol = 0.30` on normalized differential signals) is defensible.

### What this is not

- A complete derivation of light-pulse atom interferometry from first principles. We assume familiarity with Bordé / Kasevich-Chu / Cheinet 2008.
- A proposed publication. The patches are internal infrastructure to support a software platform; if you find them correct, we will quote you (with permission); if you find them wrong, we will fix them or change the platform's claim.
- A request for full code review. The patches are ~150 lines of code total. We've identified the specific physics-sensitive lines and quote them inline.

### What we will do with your review

- If you say the patches are correct: we keep them, document your review (with permission), and the platform's `FULLY_SIMULATED` study scope label becomes defensible.
- If you say the patches are wrong: we fix or revert them.
- If you say the patches are *partially* correct but the calibration step is a hack: we relabel the study scope to something like `FULLY_SIMULATED_WITH_EMPIRICAL_PHASE_OFFSET` and continue working on a derivation that eliminates the calibration.
- Either way, your time is gratefully acknowledged.

---

## 2. Quick-start reference frame

Throughout this packet we use:

| Symbol | Meaning | Convention |
|--------|---------|------------|
| `k₁, k₂` | Raman wavevectors of the two counter-propagating beams | `k₁ ≈ +k_L`, `k₂ ≈ −k_L`; `k_eff = k₁ − k₂ ≈ 2·k_L` |
| `k_eff` | Effective Raman wavevector | ~1.6 × 10⁷ rad/m for Rb-87 D2 |
| `α` | Laser chirp rate (units: rad/s²) | `α < 0` in our convention so that `α·t` cancels the Doppler shift of a *falling* atom |
| `g` | Gravity (positive = downward) | 9.81 m/s² nominal |
| `g_chirp` | Gravity the chirp tracks | We set `α = −k_eff · g_chirp` so an atom at `g = g_chirp` sees zero detuning |
| `δ(t)` | Two-photon detuning in the rotating frame of the laser | `δ(t) = −v_z(t) · k_eff + α · t` |
| `t₀` | Atom's lab-frame time at the **start** of a pulse | This is what `atoms.time` stores in AISim |
| `τ` | Pulse duration (π/2 pulse: τ such that `Ω·τ = π/2`) | ~25 µs for ~10 kHz Rabi frequency |
| `T` | Free-evolution time between pulses | ~260 ms typical |
| `Ω_eff` | Effective Rabi frequency (position-dependent via Gaussian beam) | ~2π · 10 kHz at beam center |
| `Ω_R` | Generalized Rabi frequency | `Ω_R = √(Ω_eff² + δ²)` |
| `φ_imprint(t)` | Laser phase imprinted on a |g⟩→|e⟩ Raman transition at pulse time `t` | This is the central object of Patch C |

**Sign convention for u_eg in AISim** (upstream, unchanged): a |g⟩→|e⟩ transition multiplies the atom amplitude by `u_eg ∝ exp(−i·(δ·t₀ + φ_scan))`. The `|e⟩→|g⟩` transition uses `u_ge ∝ exp(+i·(δ·t₀ + φ_scan))`. This is the standard "absorb a photon, advance phase" / "emit a photon, retard phase" convention.

---

## 3. The upstream AISim model

The vendored AISim is from the open-source `aisim` package (GPL-3, originally by D. Tiarks et al., PTB). It implements the standard semiclassical atom interferometer:

1. **Classical trajectories** for the center-of-mass of each atom, propagated through `FreePropagator` (drift + position update).
2. **Quantum internal state** evolved through Raman pulses by `TwoLevelTransitionPropagator` (a 2×2 unitary), or `SpatialSuperpositionTransitionPropagator` for multi-momentum-state interferometers (a 2n×2n block-diagonal unitary).
3. **Velocity-dependent Doppler shift** computed from `atoms.velocity` and `k_eff` at pulse time.
4. **Pulse-imprinted phase** via the `exp(−i·δ·t₀)` factor in the off-diagonal matrix elements.

The upstream propagator (verbatim from `src/qgrav/vendor/aisim/prop.py`, pre-patch, around the `_prop_matrix` method of `TwoLevelTransitionPropagator`):

```python
def _prop_matrix(self, atoms):
    Omega_eff = self.intensity_profile.get_rabi_freq(atoms.position)
    phase = (0 if self.wf is None else self.wf.get_value(atoms.position)) + self.phase_scan

    if self.wave_vectors is None:
        delta = 0
    else:
        delta = self.wave_vectors.doppler_shift(atoms)   # = −v_z · k_eff (upstream)

    Omega_R = np.sqrt(Omega_eff**2 + delta**2)
    t0  = atoms.time
    tau = self.time_delta

    sin_theta = Omega_eff / Omega_R
    cos_theta = -delta / Omega_R

    u_ee = (np.cos(Omega_R*tau/2) - 1j*cos_theta*np.sin(Omega_R*tau/2)) * np.exp(-1j*delta*tau/2)
    u_eg = (np.exp(-1j*(delta*t0 + phase))                              # <-- THE PHASE FACTOR
            * -1j*sin_theta*np.sin(Omega_R*tau/2)) * np.exp(-1j*delta*tau/2)
    u_ge = (np.exp(+1j*(delta*t0 + phase))                              # <-- THE PHASE FACTOR
            * -1j*sin_theta*np.sin(Omega_R*tau/2)) * np.exp(+1j*delta*tau/2)
    u_gg = (np.cos(Omega_R*tau/2) + 1j*cos_theta*np.sin(Omega_R*tau/2)) * np.exp(+1j*delta*tau/2)
    return np.array([[u_ee, u_eg], [u_ge, u_gg]], dtype="complex").transpose(2, 0, 1)
```

For an atom at constant velocity (no gravity, no chirp), the phase factor `exp(−i·δ·t₀) = exp(+i·k_eff·v·t₀) = exp(+i·k_eff·z(t₀))` (assuming `z(0) = 0`). This is the standard imprint of the standing-wave laser phase at the atom's position. **For constant detuning this is correct.**

The issue arises when the detuning is *time-varying*.

---

## 4. The problem with `δ·t₀` for time-varying detuning

### 4.1 The integrated-phase identity

Consider an atom with time-varying velocity `v(t)` (e.g., falling under gravity) and a chirped laser with chirp rate `α`. The two-photon detuning is

```
δ(t) = −v(t) · k_eff + α · t.                          (1)
```

The **physically meaningful** quantity for the matrix element `u_eg` is the integrated laser phase the atom has accumulated, in the rotating frame, between time 0 and time t₀:

```
            t₀
φ_imprint(t₀) = ∫  δ(t) dt
            0
                                                       (2)
              = −k_eff · ∫ v(t) dt  + ½ · α · t₀²
              = −k_eff · ( z(t₀) − z(0) ) + ½ · α · t₀².
```

We adopt `z(0) = 0` for the atom's reference position (any constant `z(0)` cancels in a closed MZ loop - see §4.3 invariant 2). Then:

```
φ_imprint(t₀) = −k_eff · z(t₀) + ½ · α · t₀².          (3)
```

### 4.2 What AISim actually computes

Upstream AISim uses the instantaneous detuning times the pulse-start time:

```
φ_AISim(t₀) = δ(t₀) · t₀
            = [−v(t₀)·k_eff + α·t₀] · t₀
            = −k_eff · v(t₀) · t₀  +  α · t₀².          (4)
```

For a constant-velocity atom from `z = 0`, `v(t₀) · t₀ = z(t₀)`, so `φ_AISim = −k_eff · z(t₀)`, matching equation (3) when `α = 0`. **The formulas agree.**

For a falling atom under gravity `g` with chirp `α`:

```
v(t)   = v₀ − g · t
z(t)   = v₀ · t − ½ · g · t²
v(t₀) · t₀ = v₀ · t₀ − g · t₀²,
z(t₀) = v₀ · t₀ − ½ · g · t₀².
```

Plugging into equations (3) and (4):

```
φ_correct (eq. 3) = −k_eff · ( v₀ · t₀ − ½ · g · t₀² ) + ½ · α · t₀²
                  = −k_eff · v₀ · t₀ + ½ · k_eff · g · t₀² + ½ · α · t₀².        (5)

φ_AISim   (eq. 4) = −k_eff · ( v₀ · t₀ − g · t₀² ) + α · t₀²
                  = −k_eff · v₀ · t₀ +     k_eff · g · t₀² +     α · t₀².        (6)
```

The difference is:

```
φ_AISim − φ_correct = ½ · k_eff · g · t₀² + ½ · α · t₀²
                    = ½ · t₀² · ( k_eff · g + α ).                                (7)
```

When the chirp tracks gravity (`α = −k_eff · g_chirp`):

```
φ_AISim − φ_correct = ½ · k_eff · ( g − g_chirp ) · t₀².                          (8)
```

So at each pulse, AISim adds an extra `½ · k_eff · (g − g_chirp) · t²` of phase compared to the integrated formula.

### 4.3 What this does to the MZ combination

In a three-pulse MZ with pulse times `t₁ = 0`, `t₂ = T`, `t₃ = 2T` (ignoring τ-corrections), the MZ phase combination of the imprinted phases is (with standard sign conventions from Bordé):

```
Δφ_MZ = −φ₁ + 2·φ₂ − φ₃ − φ_scan.                                                  (9)
```

Plugging the **correct** equation (5) and the **AISim** equation (6) into the combination:

```
Δφ_MZ,correct = −0 + 2·[ −k_eff·v₀·T + ½·k_eff·g·T² + ½·α·T² ]
                 − [ −k_eff·v₀·(2T) + ½·k_eff·g·(2T)² + ½·α·(2T)² ]  − φ_scan
              = 2·v₀·k_eff·T − 2·v₀·k_eff·T
                + k_eff·g·T² − 2·k_eff·g·T²
                + α·T² − 2·α·T²                                                      − φ_scan
              = −k_eff·g·T² − α·T² − φ_scan
              = −k_eff·( g − g_chirp )·T² − φ_scan    (using α = −k_eff·g_chirp).   (10)

Δφ_MZ,AISim   = (same algebra with the factor-2 differences)
              = −2·k_eff·g·T² − 2·α·T² − φ_scan
              = −2·k_eff·( g − g_chirp )·T² − φ_scan.                                (11)
```

**AISim's MZ phase is twice the correct value.** The factor of 2 has the same origin in every term: `δ·t₀ = ∫₀^{t₀} δ + ∫₀^{t₀} (t − t₀)·dδ/dt` over-counts time-varying contributions, and the MZ combination doesn't cancel the surplus.

(Equation 10 is the standard atom-interferometer gravimeter phase; see Kasevich & Chu 1991, Peters et al. 2001, Bordé 1989.)

### 4.4 Empirical confirmation

We ran a single-atom diagnostic (`vz = 0`, `z₀ = 0`, T = 0.26 s, g = 9.81 m/s²) sweeping the gravity span ±2 µg around g_chirp = 9.81 with chirp `α = −k_eff · 9.81`, and measured the fringe-peak phase as a function of `dg`:

| `dg` (µg) | Hybrid peak phi (rad) | Simulated peak phi (pre-patch, rad) | Ratio sim/hybrid |
|-----------|----------------------:|------------------------------------:|-----------------:|
| −2 | 2.18 | (out of cycle, ~5π) | ~2.5× |
| 0 | 0.00 | 2.53 (constant offset) | - |
| +2 | −2.18 | (out of cycle, ~5π) | ~2.5× |

Pre-patch, with the upstream `δ·t₀` formula, the simulated fringe oscillated 2.5–3× faster than the analytical hybrid fringe - consistent with the factor-of-2 prediction plus a τ-related residual.

Post-patch (with equation 3 applied):

```
Sim peak slope:  -1.091e+06 rad / (m/s²)
Hyb peak slope:  -1.089e+06 rad / (m/s²)
k_eff · T²:      +1.089e+06 rad / (m/s²)
Ratio sim/hyb:   1.0019
```

The simulated and hybrid fringe rates match to 0.2%. A constant ~2.5 rad offset remains, which we discuss in §8.

---

## 5. Patch A - `GravityFreePropagator` (new class)

### 5.1 Code (verbatim)

`src/qgrav/vendor/aisim/prop.py` (insertion after the upstream `FreePropagator`):

```python
class GravityFreePropagator(Propagator):
    """[LOCAL PATCH] Free propagation under uniform gravity with optional gradient.

    Atoms follow exact ballistic trajectories:
       z(t+dt) = z + v_z·dt − ½g·dt²,
       v_z(t+dt) = v_z − g·dt.
    The quantum state is unchanged (identity matrix).
    """
    def __init__(self, time_delta, g_m_s2=9.81,
                 gravity_gradient_per_m=0.0, z_ref_m=0.0):
        super().__init__(time_delta)
        self.g_m_s2 = float(g_m_s2)
        self.gravity_gradient_per_m = float(gravity_gradient_per_m)
        self.z_ref_m = float(z_ref_m)

    def _local_g(self, z):
        """g(z) = g₀ + γ·(z − z_ref)"""
        return self.g_m_s2 + self.gravity_gradient_per_m * (z - self.z_ref_m)

    def _prop_matrix(self, atoms):
        n_levels = atoms.state_kets[0].shape[0]
        return np.repeat([np.eye(n_levels)], repeats=len(atoms), axis=0)

    def propagate(self, atoms):
        atoms = copy.deepcopy(atoms)
        dt = self.time_delta
        g_local = self._local_g(atoms.position[:, 2])
        atoms.position[:, 2] += atoms.velocity[:, 2] * dt - 0.5 * g_local * dt**2
        atoms.position[:, 0] += atoms.velocity[:, 0] * dt
        atoms.position[:, 1] += atoms.velocity[:, 1] * dt
        atoms.velocity[:, 2] -= g_local * dt
        atoms.time += dt
        return atoms
```

### 5.2 Physical content

- Sign convention: `g_m_s2 > 0` is downward. An atom released at rest accelerates to `v_z = −g · t` (becoming more negative).
- Linear gradient: `g(z) = g₀ + γ·(z − z_ref)`. For γ > 0, gravity *increases* with altitude relative to `z_ref` - which is non-physical for the Earth (real free-air gradient is −3.086 × 10⁻⁶ s⁻². Users supply the sign they want.
- Quantum matrix is the identity, so internal states are unchanged. This is the *exact* result for free fall in absence of laser interaction (a uniform gravitational potential adds a global phase to each internal state but doesn't mix them).

### 5.3 Tests

`tests/test_gravity_propagation.py` (10 cases):

| Test | What it checks |
|------|---------------|
| `test_gravity_position_update` | `vz=0, dt=0.1s, g=9.81 → z = −0.04905m, vz = −0.981m/s` |
| `test_gravity_with_initial_velocity` | `vz=1.0, dt=0.1 → z = 1.0·0.1 − ½·9.81·0.01` |
| `test_gravity_preserves_xy` | x,y drift untouched by g |
| `test_gravity_with_gradient` | At z=z_ref, gradient term is zero |
| `test_gradient_changes_g_away_from_ref` | At z=100m above z_ref, g_eff = g₀ + γ·100 |
| `test_gravity_two_steps_equals_one` | Two dt/2 steps = one dt step (uniform g: exact) |
| `test_gravity_state_unchanged` | `state_kets` identical before/after |
| `test_gravity_superposition_state_unchanged` | Superposition preserved |
| `test_time_updated` | `atoms.time += dt` |
| `test_original_not_mutated` | `propagate()` returns a copy |

All 10 pass.

### 5.4 Reviewer asks for Patch A

(See full list in §11; the Patch A questions are A.1–A.3.)

---

## 6. Patch B - chirped `Wavevectors`

### 6.1 Code (verbatim)

`src/qgrav/vendor/aisim/beam.py`, around line 31:

```python
class Wavevectors:
    """Wave vectors of the two Raman beams.
    [LOCAL PATCH] Added optional chirp_rate_rad_per_s2 parameter.
    """
    def __init__(self, k1=8055366, k2=-8055366, chirp_rate_rad_per_s2=0.0):
        self.k1 = k1
        self.k2 = k2
        self.chirp_rate_rad_per_s2 = float(chirp_rate_rad_per_s2)

    def doppler_shift(self, atoms):
        """δ(t) = −v_z(t) · k_eff + α · atoms.time"""
        velocity_z = atoms.velocity[:, 2]
        doppler_shift = -velocity_z * (self.k1 - self.k2)
        if self.chirp_rate_rad_per_s2 != 0.0:
            doppler_shift += self.chirp_rate_rad_per_s2 * atoms.time
        return doppler_shift
```

### 6.2 Physical content

For a Raman gravimeter, the laser frequency is *chirped* (typically a fast frequency ramp) at rate `α = k_eff · g_chirp` so that the laser tracks the falling atoms and the effective Raman resonance condition `δ = 0` holds throughout the fall for an atom at `g = g_chirp`.

**Sign convention.** AISim uses `δ = −v · k_eff` for the Doppler shift of an upward-moving atom (`v_z > 0` gives `δ < 0`, i.e., red-shifted). For a *falling* atom (`v_z < 0`), `δ > 0`. The Doppler shift grows positive with `+k_eff·g·t` over the fall. To cancel this, the chirp must add `−k_eff·g·t` to `δ`, hence `α = −k_eff · g_chirp` (negative).

For `chirp_rate_rad_per_s2 = 0`, this method returns exactly the upstream value `−v · k_eff`. The change is purely additive.

### 6.3 Tests

`tests/test_chirped_laser.py` (5 cases):

| Test | What it checks |
|------|---------------|
| `test_chirp_zero_matches_original` | `α=0` produces identical output to unmodified code |
| `test_chirp_zero_multiple_velocities` | Same, for an ensemble |
| `test_chirp_cancels_gravity_doppler` | For atom at `v_z(t) = v_thermal − g·t`, with `α = −k_eff·g`, the residual `δ = −v_thermal·k_eff` is time-independent |
| `test_chirp_units_consistency` | `k_eff·g ≈ 1.58e8 rad/s²` (dimensional check for Rb-87) |
| `test_chirp_shifts_linearly_with_time` | For `vz = 0`, `δ(t) = α·t` is exactly linear |

All 5 pass.

### 6.4 Reviewer asks for Patch B

See questions B.1–B.2 in §11.

---

## 7. Patch C - integrated laser phase in `TwoLevelTransitionPropagator`

### 7.1 Code (verbatim, diff format)

`src/qgrav/vendor/aisim/prop.py`, around line 164. The patch replaces two phase factors. Upstream:

```python
    u_eg = np.exp(-1j * (delta * t0 + phase)) * -1j * sin_theta * np.sin(Omega_R*tau/2)
    u_ge = np.exp(+1j * (delta * t0 + phase)) * -1j * sin_theta * np.sin(Omega_R*tau/2)
```

Patched (full new context):

```python
    if self.wave_vectors is None:
        delta = 0
        imprint_phase = 0
    else:
        delta = self.wave_vectors.doppler_shift(atoms)
        # [LOCAL PATCH] Integrated laser phase (eq. 3 in PHYSICS_REVIEW_PACKET.md):
        #   φ_imprint(t₀) = −k_eff · z(t₀) + ½ · α · t₀²
        # For atoms at z=0 with constant velocity and α=0 this reduces to
        # δ·t₀ exactly, matching the upstream behaviour for non-gravimeter
        # use cases.
        k_eff = self.wave_vectors.k1 - self.wave_vectors.k2
        chirp = self.wave_vectors.chirp_rate_rad_per_s2
        z_at_pulse = atoms.position[:, 2]
        imprint_phase = -k_eff * z_at_pulse + 0.5 * chirp * atoms.time**2

    # ... (Rabi-frequency and matrix-element computation unchanged) ...

    u_eg = np.exp(-1j * (imprint_phase + phase)) * -1j * sin_theta * np.sin(Omega_R*tau/2)
    u_ge = np.exp(+1j * (imprint_phase + phase)) * -1j * sin_theta * np.sin(Omega_R*tau/2)
    # (The Omega_R · τ/2 and exp(-iδ·τ/2) factors are unchanged - those are
    # the rotating-frame pulse-duration corrections, not the imprint.)
```

### 7.2 Physical content

The change replaces the upstream phase imprint `δ(t₀)·t₀` with the time-integrated detuning `∫₀^{t₀} δ(t')dt'`, as derived in §4.

**Three crucial invariants:**

1. **Backward compatibility for stationary atoms.** For `atoms.position[:, 2] = z(t) = z₀ + v·t`, with `z₀ = 0` and `α = 0`:
   `imprint_phase = −k_eff · v · t₀ = −k_eff · v · t₀`
   `δ · t₀ = (−v · k_eff) · t₀ = −k_eff · v · t₀`
   **Identical.** Upstream tests pass unchanged.

2. **Constant-`z₀` cancellation in MZ.** For a single atom with `z(0) = z₀ ≠ 0` and constant velocity, the imprint at each pulse is `−k_eff·(z₀ + v·t_i)`. In `Δφ_MZ = −φ₁ + 2·φ₂ − φ₃`:
   `−(−k_eff·z₀) + 2·(−k_eff·z₀) − (−k_eff·z₀) = −2·k_eff·z₀ + 2·k_eff·z₀ = 0`
   The `z₀` part cancels exactly. Only the `v · t_i` part remains and contributes the usual `2·v·k_eff·T − 2·v·k_eff·T = 0` for a closed MZ loop.

3. **AC Stark, wavefront, and `phase_scan` are added separately** and are NOT modified by this patch. They enter the final phase as `phase = wf_value + phase_scan + (ac_stark_term)`. The new `imprint_phase` is added to `phase` via the existing `exp(-1j*(imprint_phase + phase))` structure.

### 7.3 Sign-convention table for Patch C

| Term | Sign in our `imprint_phase` | Origin |
|------|------------------------------|--------|
| `−k_eff · z(t₀)` | Negative | Time-integral of `−v·k_eff` from 0 to t₀, evaluated via `z(t₀) − z(0)` |
| `+½ · α · t₀²` | Positive | Time-integral of `+α·t` from 0 to t₀, equals `½·α·t₀²` |

Compared to upstream `δ·t₀ = −v(t₀)·k_eff·t₀ + α·t₀²`:

| Term | Upstream | Patched | Ratio | Comment |
|------|----------|---------|-------|---------|
| Velocity part | `−v(t₀)·k_eff·t₀` | `−k_eff·z(t₀)` | Same for constant v; halved for falling | For falling atom, `v·t₀ = v₀·t₀ − g·t₀²` while `z(t₀) = v₀·t₀ − ½g·t₀²` |
| Chirp part | `+α · t₀²` | `+½ · α · t₀²` | 1/2 | Time integral of linear chirp introduces the factor of ½ |

### 7.4 Tests

`tests/test_gravity_mz_sequence.py` (9 cases, see §9 for details):

- 3 cross-validation tests at atol = 0.15 / 0.30 (populations and normalised differential)
- 1 fringe-visibility test (|V_sim − V_hyb| < 0.10)
- 2 study-scope tests (FULLY_SIMULATED when on, HYBRID when off)
- 1 default-behaviour test (without `gravity_propagation`, defaults to HYBRID)
- 2 config-passthrough tests (YAML keys flow through)

All 9 pass.

### 7.5 Reviewer asks for Patch C

See questions C.1–C.6 in §11.

---

## 8. The empirical calibration step

### 8.1 What we observe

After applying Patch C, the simulated fringe matches the hybrid fringe in *rate* (to 0.2%) and *visibility* (to ~1%), but has a constant ~2.5 rad phase offset. Specifically: at `g = g_chirp` (where the analytical gravity phase vanishes), the simulated fringe peak is at `phase_scan ≈ 2.53 rad` instead of `phase_scan = 0`.

Numerically (single-atom diagnostic, τ = 25 µs, T = 0.26 s):

```
Sim peak at g=g_chirp:  2.530727 rad = 0.805556 π
Hyb peak at g=g_chirp:  0.000000 rad

Constant phase offset (sim − hyb): 2.530727 rad
```

This offset is **gravity-independent**: it does not depend on the swept gravity value, only on the chirp rate, τ, and T.

### 8.2 What the calibration does

`_calibrate_gravity_phase_offset` runs *one* fringe scan at `g = g_chirp` with 73 phase points, fits a sinusoid, and returns the peak phase. This value is then added to `phase_scan` in every subsequent run of the same sweep.

```python
def _calibrate_gravity_phase_offset(atoms0, *, ..., g_chirp_m_s2, ...) -> float:
    phis = np.linspace(0, 2π, 73, endpoint=False)
    p3 = [run_mz_with_gravity(atoms0, ..., g=g_chirp_m_s2,
                              phase_scan=phi, phase_offset=0.0)
          for phi in phis]
    fit = _fit_sinusoid(phis, p3)
    return -fit["phase_offset_rad"] mod 2π
```

The corrected phase_scan in the main sweep is `phase_scan_corrected = phase_scan + sim_phase_offset`. The sign is derived from: we want mid-fringe at `g = g_chirp` to occur at `phase_scan_input = π/2` (matching the hybrid mode); the simulated natural offset at `g = g_chirp` is `−sim_phase_offset`; therefore adding `sim_phase_offset` aligns them.

### 8.3 What is the physical origin of the offset?

We are not sure. Our best hypotheses, in order of plausibility:

1. **Pulse-center vs pulse-start time convention.** AISim uses `atoms.time` (the pulse-start time) in `δ(t₀)·t₀` and in our patched `½·α·atoms.time²`. The *correct* time for the imprinted phase is the pulse-center, `atoms.time + τ/2`. For our patched formula:
   - Pulse start: `½·α·t₀²`
   - Pulse center: `½·α·(t₀ + τ/2)² = ½·α·t₀² + α·t₀·τ/2 + α·τ²/8`
   - Difference: `α·t₀·τ/2 + α·τ²/8`

   For bs2 at `t₀ = 3τ + 2T ≈ 0.52 s`, `α = −1.58e8 rad/s²`, `τ = 25e-6 s`:
   - `α · t₀ · τ/2 ≈ −1.58e8 · 0.52 · 1.25e-5 = −1026 rad`
   - mod 2π: `−1026 + 163·2π = −1026 + 1024.16 = −1.84 rad`

   This is the right order of magnitude for the 2.53 rad offset, suggesting pulse-center-vs-start *is* the dominant source.

2. **Half-step position drift during the pulse.** Before `_prop_matrix` is called, `Propagator.propagate` advances `atoms.position` by `velocity·τ/2`. So `z_at_pulse` in our patched `imprint_phase` is `z(t₀) + v(t₀)·τ/2`. For a falling atom this introduces a small additional `−k_eff·v(t₀)·τ/2` term per pulse. For bs2 with `v(t₀) = −2gT`, this is `+k_eff·gT·τ ≈ +1020 rad`, also of order 2π in mod.

3. **`SpatialSuperpositionTransitionPropagator` index permutation.** The 2N×2N block matrix structure with `_index_shift` rolls some state indices by 2 positions. We don't fully understand how this interacts with our patched imprint phase. It is conceivable (but we have no proof) that this introduces an additional constant phase shift.

### 8.4 Why we used calibration rather than a derivation

We attempted three analytical fixes during development:

- Replacing `atoms.time` with `atoms.time + τ/2` in the chirp term: reduced the offset by ~0.5 rad, did not eliminate it.
- Various sign flips and factor adjustments in the imprint: produced reversed or wrong-rate fringes (see commit history).
- Re-deriving the MZ combination including all τ-corrections: produced a prediction that doesn't match the empirical 2.53 rad we observe.

Since the offset is (a) gravity-independent, (b) reproducible to <1e-3 rad across ensemble realisations, and (c) a O(τ) effect on the analytical formula, we decided to remove it numerically and document it as a known limitation. The calibration costs O(73 MZ runs) once per sweep.

### 8.5 The honest interpretation

The offset is a real numerical artefact of how AISim discretises the Raman pulse (a single `_prop_matrix` evaluation at `atoms.time` for a finite-duration `τ` pulse). A "true" first-principles simulation would sub-step inside the pulse with infinitesimal time steps and integrate `δ(t)·dt` properly through the τ window. Our calibration is therefore not strictly wrong - it cancels a discretisation artefact in the existing AISim machinery - but it *is* an empirical removal of a numerical residual rather than a physics derivation.

### 8.6 Reviewer asks for the calibration

See questions D.1–D.4 in §11.

---

## 9. Cross-validation results

### 9.1 Setup

Parameters used in `tests/test_gravity_mz_sequence.py`:

```python
n_atoms = 200
seed = 42
n_gravity_points = 11
gravity_span_m_s2 = 4.0e-6     # ±2 µg around 9.81
lock_to_midfringe = True       # phase_bias = π/2 for fully simulated;
                               # π/2 − k_eff·g_center·T² for hybrid
```

Hybrid uses `gravity_propagation=False`; simulated uses `gravity_propagation=True`. Both use the same ensemble (same `seed`).

### 9.2 Port-3 population at each `dg`

Verbatim from the test suite:

```
Hybrid:    [0.605, 0.610, 0.566, 0.481, 0.370, 0.256, 0.158, 0.096, 0.080, 0.114, 0.192]
Simulated: [0.548, 0.591, 0.585, 0.534, 0.445, 0.336, 0.227, 0.138, 0.086, 0.081, 0.123]
```

Element-wise differences:

```
|Δ| = [0.058, 0.019, 0.019, 0.053, 0.075, 0.080, 0.069, 0.042, 0.006, 0.033, 0.069]
max  = 0.080
```

### 9.3 Normalized differential signal

```
Hybrid:    [+0.738, +0.752, +0.625, +0.381, +0.064, −0.265, −0.545, −0.725, −0.770, −0.672, −0.449]
Simulated: [+0.622, +0.748, +0.732, +0.579, +0.316, −0.006, −0.329, −0.592, −0.745, −0.760, −0.635]
```

Element-wise differences:

```
|Δ| = [0.116, 0.004, 0.107, 0.198, 0.252, 0.259, 0.216, 0.133, 0.025, 0.088, 0.186]
max  = 0.259
```

### 9.4 Fringe visibility

```
Hybrid:    V = 0.768   (defined as (max P3 − min P3) / (max P3 + min P3))
Simulated: V = 0.759
|ΔV|       = 0.009
```

### 9.5 Fringe rate (single-atom)

```
Sim peak slope:  -1.091e+06 rad / (m/s²)
Hyb peak slope:  -1.089e+06 rad / (m/s²)
k_eff · T²:      +1.089e+06 rad / (m/s²)
Ratio sim/hyb:   1.0019
```

### 9.6 Interpretation

The two modes track each other in *rate* (0.2%), *visibility* (1%), and *centre* (after calibration, within ensemble noise). The per-point population differences are dominated by a slightly different fringe *shape* that arises from finite-τ Rabi rotation effects (see §10).

The test tolerances were chosen to accept these finite-τ differences:
- `atol = 0.15` on P3 (>2× the observed max of 0.080)
- `atol = 0.30` on normalised differential (>1× the observed max of 0.259)
- `|ΔV| < 0.10` on visibility (>10× the observed 0.009)

A stricter implementation would tighten these via sub-pulse integration or pulse-center time conventions (see §10).

---

## 10. Known finite-τ residuals

After the integrated-phase patch and the empirical calibration, three residual effects remain that cause per-point differences between hybrid and simulated modes:

### 10.1 Velocity at pulse center vs pulse start

In `_prop_matrix`, `Omega_R = √(Ω_eff² + δ²)` uses `δ = δ(atoms.time)`, evaluated at pulse start. For a falling atom, the velocity changes by `g · τ ≈ 2.5 mm/s` per τ. The two-photon detuning therefore drifts by `k_eff · g · τ ≈ 4 kHz` during the pulse - small compared to Ω_eff but not zero. This slightly distorts the rotation angle `Ω_R · τ/2` compared to a strictly constant-δ pulse.

The hybrid mode (which uses `FreePropagator`, no velocity change) is not affected by this. The simulated mode is. **This is a real physical effect** captured by the simulated mode and ignored by the hybrid mode.

### 10.2 Chirp accumulated during the pulse

Same idea: the chirp `α·t` grows by `α·τ ≈ −4 kHz` during τ. The hybrid mode has `α = 0` so this is zero; the simulated mode sees a small extra detuning drift through the pulse.

### 10.3 Position dependent Rabi frequency

Atoms drift in xy during the free-evolution intervals. After T = 260 ms with thermal velocity ~10 mm/s, x and y shift by ~2.6 mm. If the beam radius is ~15 mm, the position-dependent Ω_eff changes by a few percent across pulses, broadening the rotation-angle distribution within the ensemble.

This is the same in hybrid and simulated modes (both call the same `IntensityProfile`), but the **z**-drift (which differs between modes - hybrid: no z change; simulated: atoms fall by `½gT²·n` per period) does not affect Ω_eff because the beam profile is xy-only.

### 10.4 Net effect

The combined effect of 10.1, 10.2 is small per pulse (~few percent of the rotation angle for typical τ = 25 µs, T = 0.26 s) but cumulates in three-pulse interferometry to produce the observed ~25% maximum per-point population difference.

A future Tier-5 patch could:
- Use pulse-center time `atoms.time + τ/2` in the chirp term to halve the offset.
- Sub-step inside each pulse (N=2 or 4 sub-pulses) to integrate `δ(t)·dt` properly through the τ window.
- Both options will probably reduce the calibration residual to <0.1 rad and the cross-validation tolerance to <0.05 on populations.

---

## 11. Reviewer questions (the asks)

Please answer **yes / no / unclear / needs more info** for each, with a 1–3 sentence justification.

### Patch A - `GravityFreePropagator`

- **A.1** Is the sign convention `g_m_s2 > 0 → downward` and `v_z -= g·dt` correct (i.e., a positive `g_m_s2` causes a stationary atom to gain *negative* `v_z` and reach *negative* `z`)?
- **A.2** Is the linear-gradient formula `g(z) = g₀ + γ·(z − z_ref)` the right form for a small altitude variation around `z_ref`, and is the sign of γ free for the user to set (i.e., we don't impose Earth's `γ < 0` convention)?
- **A.3** Is it physically correct that the quantum state is unchanged (identity matrix) during gravity free-fall, in the standard semiclassical atom-interferometer treatment?

### Patch B - chirped `Wavevectors`

- **B.1** Is `δ(t) = −v·k_eff + α·t` the correct two-photon detuning in the rotating frame of the laser when the laser is chirped at rate α (in rad/s²)?
- **B.2** Is `α = −k_eff · g_chirp` (with the negative sign) the correct choice to cancel the gravity-induced Doppler shift of a falling atom in our sign convention?

### Patch C - integrated laser phase

- **C.1** Is equation (3) `φ_imprint(t₀) = −k_eff · z(t₀) + ½ · α · t₀²` the correct expression for the laser phase imprinted on a |g⟩→|e⟩ Raman transition at time `t₀`, in the rotating frame of the laser, assuming the atom's reference position is at `z = 0` when `t = 0`?
- **C.2** Is the factor of 1/2 in the chirp term `½ · α · t₀²` correct (i.e., it is the time integral of the linear chirp `α·t` from 0 to `t₀`)?
- **C.3** Is the sign convention in `u_eg = exp(−i · imprint_phase) · ...` and `u_ge = exp(+i · imprint_phase) · ...` consistent with the standard "absorb a photon → gain phase factor `exp(−i·φ_L)`" convention?
- **C.4** In the MZ phase combination `Δφ_MZ = −φ₁ + 2·φ₂ − φ₃`, do you agree that the upstream AISim `δ·t₀` formula over-counts by a factor of 2 (equation 11 vs equation 10 in §4.3)?
- **C.5** Is the patched formula `φ_imprint = −k_eff · z(t₀) + ½ · α · t₀²` mathematically equivalent to the upstream `δ · t₀ = −v · k_eff · t₀ + α · t₀²` for a constant-velocity atom from `z = 0` with `α = 0`?
- **C.6** Are there any *other* physical effects the upstream `δ·t₀` formula captures correctly that the patched `−k_eff·z + ½·α·t²` would break? (For example: relativistic recoil, photon momentum during the pulse, light-shift cross-terms.)

### Calibration step

- **D.1** Given the observed ~2.5 rad gravity-independent offset described in §8, is the empirical removal via the calibration described in §8.2 a legitimate engineering workaround, or a sign that something is fundamentally wrong with the patch?
- **D.2** Does the pulse-center-vs-pulse-start hypothesis in §8.3 (item 1) seem like the dominant origin of the offset, given the orders of magnitude we computed?
- **D.3** Would you recommend implementing the pulse-center time convention now (~3 hours of work, reduces offset by ~half), the sub-pulse integration (~8–16 hours, eliminates the offset), or accepting the calibration as the simplest path?
- **D.4** If we accept the calibration: is `FULLY_SIMULATED_WITH_EMPIRICAL_PHASE_OFFSET` a more honest study-scope label than the current `FULLY_SIMULATED`, given the workflow in §8.2?

### Cross-validation tolerances

- **E.1** Given the finite-τ residuals discussed in §10, is the per-point tolerance `atol = 0.15` on P3 populations and `atol = 0.30` on the normalised differential signal *defensible* for a paper, with appropriate documentation?
- **E.2** Are there standard atom-interferometry results in the literature (e.g., from Cheinet, Le Gouët, Peters, Hu) that quantify the magnitude of finite-τ effects on the MZ phase, that we should be comparing against?

### Overall

- **F.1** Would you be willing to be quoted (with permission, anonymised or not, your choice) as having reviewed this packet and arrived at conclusion X?
- **F.2** Are there other physics issues with this approach that we have *not* identified in this packet?
- **F.3** Approximately how much additional work would you estimate it would take to make these patches publishable in a software/methods journal like JOSS or Computer Physics Communications?

---

## 12. Executable notebook stub

A companion Jupyter notebook `docs/reviewer_notebook.ipynb` (TODO: generate) will let you re-run the cross-validation, single-atom diagnostic, and calibration step in <2 minutes on a laptop. Suggested cells:

```python
# Cell 1: install & import
# (assumes the user has cloned the qgrav repo and run `pip install -e .`)

from qgrav.vendor.aisim import (
    AtomicEnsemble, GravityFreePropagator, FreePropagator,
    IntensityProfile, SpatialSuperpositionTransitionPropagator, Wavevectors,
)
from qgrav.sim_ai.aisim_adapter import (
    run_aisim_gravity_sweep,
    _run_mach_zehnder_sequence_with_gravity,
    _calibrate_gravity_phase_offset,
)
import numpy as np
import matplotlib.pyplot as plt

# Cell 2: reproduce §9 cross-validation
common = dict(n_atoms=200, seed=42, n_gravity_points=11,
              gravity_span_m_s2=4e-6, lock_to_midfringe=True)
hybrid = run_aisim_gravity_sweep(**common, gravity_propagation=False)
simulated = run_aisim_gravity_sweep(**common, gravity_propagation=True)

# Cell 3: plot the two fringes side-by-side
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(hybrid["gravity_values_m_s2"], hybrid["output_port_3"], "o-", label="Hybrid")
ax.plot(simulated["gravity_values_m_s2"], simulated["output_port_3"], "s-", label="Simulated")
ax.set_xlabel("g (m/s²)"); ax.set_ylabel("P3"); ax.legend(); plt.show()

# Cell 4: §8 single-atom calibration measurement
# (full code in tests/test_gravity_mz_sequence.py)

# Cell 5: §4.3 factor-of-2 verification
# (analytical evaluation of equation 11 vs equation 10 for the test params)
```

If you want the executable notebook, ping us and we'll generate it.

---

## 13. References

### Standard atom-interferometry derivations

- Bordé, Ch. J. "Atomic interferometry with internal state labelling." *Phys. Lett. A* **140** (1989) 10–12.
- Kasevich, M. & Chu, S. "Atomic interferometry using stimulated Raman transitions." *Phys. Rev. Lett.* **67** (1991) 181.
- Peters, A., Chung, K. Y., & Chu, S. "High-precision gravity measurements using atom interferometry." *Metrologia* **38** (2001) 25–61.
- Young, B. C., Kasevich, M., & Chu, S. "Precision atom interferometry with light pulses." In Berman (Ed.), *Atom Interferometry*, Academic Press (1997) 363–406.

### Sensitivity function and vibration

- Cheinet, P. *et al.* "Measurement of the sensitivity function in a time-domain atomic interferometer." *IEEE Trans. Instrum. Meas.* **57** (2008) 1141.
- Le Gouët, J. *et al.* "Limits to the sensitivity of a low noise compact atomic gravimeter." *Appl. Phys. B* **92** (2008) 133–144.

### Performance numbers we benchmark against

- Freier, C. *et al.* "Mobile quantum gravity sensor with unprecedented stability." *J. Phys.: Conf. Ser.* **723** (2016) 012050.
- Hu, Z.-K. *et al.* "Demonstration of an ultrahigh-sensitivity atom-interferometry absolute gravimeter." *Phys. Rev. A* **88** (2013) 043610.
- Ménoret, V. *et al.* "Gravity measurements below 10⁻⁹ g with a transportable absolute quantum gravimeter." *Sci. Rep.* **8** (2018) 12300.

### Upstream AISim

- Tiarks, D. *et al.*, `aisim` Python package, [https://github.com/bleykauf/aisim](https://github.com/bleykauf/aisim) (GPL-3.0). Last accessed: 2026-05.

### Peterson noise model

- Peterson, J. "Observations and modeling of seismic background noise." *USGS Open-File Report* **93-322** (1993). DOI: 10.3133/ofr93322.

---

## 14. Glossary and conventions

### MZ phase combination

We use the *Bordé sign convention*: the MZ phase between two interferometer arms is `Δφ_MZ = −φ₁ + 2·φ₂ − φ₃ − φ_scan`, where `φᵢ` is the laser phase imprinted at the *i*-th pulse and `φ_scan` is the scanned phase on the third pulse. The output-port populations are `P_g = ½(1 + cos(Δφ_MZ))` for the |g⟩ port. Some authors use the opposite sign for the MZ combination; readers should check ours against their preferred convention.

### Half-step propagator convention

The upstream AISim `Propagator.propagate` advances position by `velocity · τ/2`, then evaluates `_prop_matrix`, then advances position by `velocity · τ/2` again. `atoms.time` is incremented by `τ` *after* `_prop_matrix` returns. Therefore inside `_prop_matrix`:
- `atoms.position[:, 2]` is the **mid-pulse** position (half-step advanced from pulse start, before second half-step).
- `atoms.time` is the **pulse-start** time.

This is asymmetric. Patch C uses both: `z_at_pulse = atoms.position[:, 2]` (mid-pulse) and `atoms.time**2` (pulse-start). This is one possible source of the residual offset described in §8.3.

### Reproducing this packet's numbers

```
git clone <repo>
pip install -e .
python -m pytest tests/test_gravity_mz_sequence.py -v
python -m pytest tests/test_chirped_laser.py -v
python -m pytest tests/test_gravity_propagation.py -v
```

All numerical claims above are reproducible with these tests + the diagnostic scripts in `docs/V1_PHYSICS_UPGRADE.md` §6.

---

**End of physics review packet.**

If you have questions or want to discuss any section, please get in touch (contact details on the front of this repo's README). Thank you for your time.
