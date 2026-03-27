from __future__ import annotations

import numpy as np

def curve_correlation(x1: np.ndarray, y1: np.ndarray, x2: np.ndarray, y2: np.ndarray) -> dict[str, float]:
    """Interpolate curve 2 onto curve 1 grid (overlap only) and compute corr + R²."""
    x1 = np.asarray(x1, dtype=np.float64)
    y1 = np.asarray(y1, dtype=np.float64)
    x2 = np.asarray(x2, dtype=np.float64)
    y2 = np.asarray(y2, dtype=np.float64)

    xmin = max(np.min(x1), np.min(x2))
    xmax = min(np.max(x1), np.max(x2))
    if xmax <= xmin:
        raise ValueError("Curves do not overlap.")

    mask = (x1 >= xmin) & (x1 <= xmax)
    x = x1[mask]
    if len(x) < 5:
        raise ValueError("Not enough overlap.")
    y1i = y1[mask]
    y2i = np.interp(x, x2, y2)

    y1z = y1i - np.mean(y1i)
    y2z = y2i - np.mean(y2i)
    denom = np.sqrt(np.sum(y1z**2) * np.sum(y2z**2))
    corr = float(np.sum(y1z * y2z) / denom) if denom > 0 else float("nan")

    ss_res = float(np.sum((y1i - y2i) ** 2))
    ss_tot = float(np.sum((y1i - np.mean(y1i)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")

    return {"corr": corr, "r2": float(r2)}
