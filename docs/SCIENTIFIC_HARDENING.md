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
