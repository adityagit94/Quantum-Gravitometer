# Project Specification (Frozen Definitions)

This document exists to prevent scope drift and to make claims **measurable**.

## 1) What we are building (software-first, zero-lab)

An integrated pipeline that:
1. Generates **simulation outputs** (atom interferometer + noise model). **v1.0:** gravity phase emerges from a ballistic atom trajectory under a chirped Raman laser; the closed-form `k_eff·g·T²` formula is no longer required.
2. Generates **virtual measurement data** (interferometer I/Q channels + drift/noise; v1.0 adds Peterson NLNM/NHNM time-domain vibration traces with optional isolation filtering)
3. Runs **two estimators** (baseline vs improved)
4. Computes **metrics** (PSD, Allan deviation, correlation/R²; **v1.0** adds per-drop Allan deviation from the multi-drop cycle simulator)
5. Produces a **reproducible report** from a single config file.

Hardware is intentionally out-of-scope for this repository version.

---

## 2) Metrics and definitions

### 2.1 “Simulation accuracy < 1%”
Defined only for **benchmark cases where a reference is unambiguous**.

Hybrid-mode (default) reference:
- `phi_ref = k_eff * a * T^2`

Accuracy metric:
- Relative error: `abs(phi_sim - phi_ref) / max(abs(phi_ref), eps)` must be `< 0.01`.

In hybrid mode (`gravity_propagation: false`) the AISim adapter literally evaluates this formula and feeds it as the final beamsplitter phase scan. The benchmark is therefore exact (< 1e-10 rad) and is enforced by the truth check `analytic_phase_match` in `_check_gravity_sweep`.

**v1.0 - fully simulated reference:**

When `gravity_propagation: true`, the gravity phase is no longer evaluated from a closed form. Instead it emerges from the AISim matrix-element multiplication after the patched integrated-phase formula. The new benchmark is a **cross-validation** between the two modes:

- Run the same gravity sweep with `gravity_propagation: false` and with `gravity_propagation: true`.
- Compare the resulting port populations, normalized differential signals, and fringe visibilities.

Pass criteria (`tests/test_gravity_mz_sequence.py`):
- `|P3_sim − P3_hybrid| < 0.15` at each gravity point.
- `|normalized_diff_sim − normalized_diff_hybrid| < 0.30`.
- `|visibility_sim − visibility_hybrid| < 0.10`.
- Fringe rate matches `k_eff · T²` to within 1% (verified at single-atom granularity).

The non-trivial atol arises from finite-Raman-pulse-duration physics (chirp τ-residuals during pulses change the Rabi rotation slightly); it is a real physical effect that the simulated mode captures and the analytical formula ignores.

### 2.2 “Noise reduction by 50%”
Measured using **RMSE displacement error** against ground truth (virtual bench):

- `RMSE = sqrt(mean((x_hat - x_true)^2))`

Noise reduction claim:
- `RMSE_improved <= 0.5 * RMSE_baseline` on the configured dataset.

(You can swap to Allan deviation or integrated PSD later, but freeze it before comparing.)

### 2.3 “Agreement / correlation >= 0.95”
Agreement between two curves (e.g., PSD curves) defined using:
- Pearson correlation on log-PSD values after interpolation to a common frequency grid.
- R² on the same comparison.

Pass criteria:
- `corr >= 0.95` (and/or `R2 >= 0.95`) for the specified evaluation band.

---

## 3) Definition of done (MVP)

A single command:
```bash
qgrav run --config configs/example.yaml
```

Creates:
- `config_used.yaml`
- `data.npz` (truth + measured I/Q + estimates)
- `metrics.json`
- `plots/*.png`
- `report.html`

And tests pass:
```bash
pytest -q
```

---

## 4) Upgrade path (when resources appear)

Completed in v1.0:
- Replaced minimal atom interferometer model with high-fidelity AISim integration.
- Added `bench_ifo/real_ifo.py` and `bench_ifo/real_gravity.py` honouring the same keys as `virtual_ifo.generate_virtual_ifo`.
- Promoted `gravity_sweep` and `vibration_sensitivity_sweep` from HYBRID to optionally FULLY_SIMULATED (`gravity_propagation: true`).
- Added `multi_drop_cycle` for end-to-end gravimeter-campaign simulation.

Remaining future work:
- Real photodiode data ingestion (separate from the synthetic virtual interferometer).
- Replace the analytical sinusoidal mirror motion in `vibration_sensitivity_sweep` with a time-domain mirror displacement fed from `generate_vibration_timeseries` (a `vibration_model="time_domain"` switch is left for a follow-up release).
- Drop-to-drop seismic-drift correlations in `multi_drop_cycle` (currently each drop is statistically independent).
- Anti-windup and non-linear extensions to the `servo_integrator_step` integrator.

Keep metrics + reporting identical to preserve comparability.
