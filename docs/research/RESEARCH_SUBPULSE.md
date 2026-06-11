# Sub-Pulse Integration of Finite-Duration Raman Pulses (`raman_substeps`)

*Design + validation note for the v1.5 `raman_substeps` feature. Companion to
`RESEARCH_FINITE_TAU.md` / `RESEARCH_FINITE_TAU_FORMULAS.md`, which hold the
literature derivations.*

## What it does

Before v1.5 each Raman pulse was applied as **one** rotation matrix evaluated
once for the whole pulse: atoms drift at constant velocity during the pulse
(no gravity), the Rabi frequency / Doppler detuning / laser-phase imprint are
sampled a single time. That single-matrix discretisation produces a known
finite-pulse artefact — a constant, gravity-independent fringe offset (~0.86 rad
for the exaggerated parameters below; ~1.1 rad for GAIN parameters per the
v1.2 study) — which `_calibrate_gravity_phase_offset` removes empirically, and
it misses the finite-τ scale-factor physics entirely (the simulated gravity
phase is `k_eff·Δg·T²` with **no** τ correction).

With `raman_substeps: N > 1`
(`IntegratedPhaseSpatialSuperpositionTransitionPropagator.propagate` in
`_aisim_overrides.py`), each pulse of duration τ is applied as N composed
slices of τ/N:

1. **half-slice ballistic fall** — position *and velocity* update under
   `g` (+ optional linear gradient), exactly the `GravityFreePropagator`
   kinematics;
2. **slice rotation matrix** evaluated at the slice **midpoint**: mid-slice
   position (Gaussian-beam Rabi frequency and the `−k_eff·z` imprint),
   mid-slice velocity (Doppler detuning), mid-slice time (the chirp term in
   both the detuning and the `½·chirp·t²` imprint);
3. **second half-slice fall**.

As N → ∞ the composition converges to the time-ordered evolution of the
two-level Hamiltonian with the time-dependent laser phase, so the pulse-timing
physics **emerges** numerically. `raman_substeps = 1` (default) takes the
original upstream code path and is bit-identical to v1.4 output
(regression-tested with fixed seeds).

## Discretisation choices

- **Midpoint sampling** (position/velocity/time at slice centre): second-order
  accurate per slice; empirically the φ(N) sequence contracts by ~0.35× per
  doubling of N (see numbers below).
- **Gravity inside the pulse**: the substep path needs `g` at pulse-apply
  time, so `_run_mach_zehnder_sequence_with_gravity` forwards
  `substep_g_m_s2` / `substep_gravity_gradient_per_m` / `substep_z_ref_m`
  to the three pulse propagators. The N = 1 path ignores them.
- **Calibration consistency**: `_calibrate_gravity_phase_offset` runs with the
  *same* N as the main sequence — the artefact it measures is N-dependent
  (≈ 1/N, see below).
- **Vendored AISim untouched**: everything lives in the override subclass
  (`tests/test_vendor_aisim_unmodified.py` still enforces byte-identity).

## Convention bookkeeping (the recurring finite-τ trap)

In this simulation `T` is the **free-evolution time between pulse edges**
(the `GravityFreePropagator(T)` span). Pulse centres are therefore spaced
`T_cc = T + 3τ/2`, and Bertoldi's `T_B` (their free interval is `T_B − 2τ`)
maps to `T_B = T + 2τ`. Substituting either convention into its respective
published form gives the *same* prediction for the emergent scale factor:

```
Fang/Mielec 2018:  S/k_eff = (T_cc + τ/2)(T_cc + (4/π − 3/2)τ) = (T + 2τ)(T + 4τ/π)
Bertoldi 2019:     S/k_eff = T_B²(1 − (2π−4)/π · τ/T_B)        = (T + 2τ)(T + 4τ/π)
```

so the cross-check target is `φ_pred = k_eff·Δg·(T + 2τ)(T + 4τ/π)`.

## Measured validation numbers

Setup: 60–80 atoms, ~1 nK–1 pK, beam radius 0.5 m, Ω·τ = π/2 on axis,
τ = 2 ms, T = 50 ms (η = τ/T = 0.04 — exaggerated so the ~3% correction is
far above fit resolution), Δg = 2×10⁻⁵ m/s², 49–73-point fringe scans
(deterministic; no shot noise in the ensemble mean).

| N  | φ_g (rad)  | offset at g_chirp (rad) |
|----|------------|--------------------------|
| 1  | −0.80420   | −0.85958                 |
| 2  | −0.91459   | +0.05469                 |
| 4  | −0.91289   | +0.02763                 |
| 8  | −0.91231   | +0.01381                 |
| 16 | −0.91212   | +0.00690                 |
| 32 | −0.91204   | +0.00345                 |

- **Convergence:** |φ(2N) − φ(N)| = 0.110, 1.7e−3, 5.8e−4, 2.0e−4, 7.8e−5 —
  every successive ratio < 0.6 (typically ~0.35).
- **Cross-check:** φ_pred = 0.914053 rad; |φ(32)| = 0.912038 rad → relative
  agreement **2.2×10⁻³**, consistent with the neglected O(η²) ≈ 1.6×10⁻³
  terms. Test tolerance: 1×10⁻² (≈4× margin).
- **N = 1 baseline:** |φ(1)| ≈ k_eff·Δg·T² to ~0.1% at 1 nK; at 1 pK it
  shifts ~2% because Bertoldi's single-shot Eq. 32 residual
  (−4θ²sin 2φ₂) no longer velocity-averages away — visible, expected, and
  removed by the substep path.
- **Artefact removal:** the g-independent calibration offset falls ≈ 1/N
  (−0.86 rad → +0.0035 rad at N = 32), confirming the v1.2 diagnosis that it
  is a pure discretisation artefact.

## Cost and guidance

Runtime scales linearly with N inside pulses only (free evolution is a single
step), so a gravity sweep at N = 8 costs roughly `1 + 4·(8−1)·τ/T_total`
more matrix work — negligible for realistic η ~ 10⁻⁴, noticeable only in the
exaggerated test geometry. For published-reference reproductions
(η ≈ 10⁻⁴–10⁻⁵) the closed-form correction is ≤ 10⁻⁴ relative, so N = 1
remains the right default; use N ≥ 8 when studying pulse-duration systematics
directly. The "fully simulated" scope label is unchanged — sub-pulse
integration *strengthens* it (one more analytic ingredient now emerges).

— 2026-06-11, v1.5 development.
