# Project Specification (Frozen Definitions)

This document exists to prevent scope drift and to make claims **measurable**.

## 1) What we are building (software-first, zero-lab)

An integrated pipeline that:
1. Generates **simulation outputs** (atom interferometer + noise model)
2. Generates **virtual measurement data** (interferometer I/Q channels + drift/noise)
3. Runs **two estimators** (baseline vs improved)
4. Computes **metrics** (PSD, Allan deviation, correlation/R²)
5. Produces a **reproducible report** from a single config file.

Hardware is intentionally out-of-scope for this repository version.

---

## 2) Metrics and definitions

### 2.1 “Simulation accuracy < 1%”
Defined only for **benchmark cases where a reference is unambiguous**.

Current MVP reference:
- `phi_ref = k_eff * a * T^2`

Accuracy metric:
- Relative error: `abs(phi_sim - phi_ref) / max(abs(phi_ref), eps)` must be `< 0.01`.

This repo currently uses the same formula for both in the minimal model, so the benchmark demonstrates the test harness. When you upgrade the simulator, keep the same benchmark suite.

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

- Replace virtual bench with real photodiode data:
  - Add `bench_ifo/real_ifo.py` returning the same keys as `virtual_ifo.generate_virtual_ifo`.
- Replace minimal atom interferometer model with higher fidelity:
  - Add a simulator adapter in `sim_ai/`.

Keep metrics + reporting identical to preserve comparability.
