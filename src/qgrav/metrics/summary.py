from __future__ import annotations

import numpy as np


def compute_error_statistics(y_true: np.ndarray, y_hat: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true, dtype=np.float64)
    y_hat = np.asarray(y_hat, dtype=np.float64)
    if y_true.shape != y_hat.shape:
        raise ValueError("Shapes must match for error statistics.")
    err = y_hat - y_true
    rmse = float(np.sqrt(np.mean(err**2)))
    mae = float(np.mean(np.abs(err)))
    max_abs = float(np.max(np.abs(err)))
    bias = float(np.mean(err))
    err_std = float(np.std(err))
    denom = float(np.sqrt(np.mean(y_true**2)))
    nrmse = float(rmse / denom) if denom > 0 else float("nan")

    signal_var = float(np.var(y_true))
    noise_var = float(np.var(err))
    snr_db = float(10.0 * np.log10(signal_var / noise_var)) if signal_var > 0 and noise_var > 0 else float("nan")

    corr = float(np.corrcoef(y_true, y_hat)[0, 1]) if len(y_true) > 1 else float("nan")
    return {
        "rmse": rmse,
        "mae": mae,
        "max_abs_error": max_abs,
        "bias": bias,
        "error_std": err_std,
        "nrmse": nrmse,
        "time_corr": corr,
        "snr_db": snr_db,
    }


def improvement_percent(baseline_value: float, improved_value: float) -> float:
    if baseline_value == 0:
        return float("nan")
    return float(100.0 * (baseline_value - improved_value) / abs(baseline_value))
