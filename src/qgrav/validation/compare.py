from __future__ import annotations

import numpy as np


def curve_correlation(
    x1: np.ndarray, y1: np.ndarray, x2: np.ndarray, y2: np.ndarray
) -> dict[str, float]:
    """Interpolate curve 2 onto curve 1 grid (overlap only) and compute corr + R-squared.

    Parameters
    ----------
    x1, y1 : reference curve (defines the evaluation grid)
    x2, y2 : comparison curve (interpolated onto x1's grid)

    Returns
    -------
    dict with 'corr' (Pearson correlation) and 'r2' (coefficient of determination).

    Notes
    -----
    Pearson correlation is symmetric: corr(y1, y2) == corr(y2, y1).

    R-squared is asymmetric. It is computed as 1 - SS_res/SS_tot where SS_tot
    is based on y1 (the reference). Swapping the roles of y1 and y2 generally
    gives a different R-squared value. R-squared can also be negative if the
    comparison curve is a worse predictor than a horizontal line at the mean.
    """
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
