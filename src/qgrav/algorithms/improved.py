from __future__ import annotations

import numpy as np


def _ewma(x: np.ndarray, alpha: float) -> np.ndarray:
    y = np.empty_like(x, dtype=np.float64)
    y[0] = float(x[0])
    a = float(alpha)
    for i in range(1, len(x)):
        y[i] = a * float(x[i]) + (1.0 - a) * y[i - 1]
    return y


def _moving_average(x: np.ndarray, window: int) -> np.ndarray:
    w = int(window)
    if w <= 1:
        return x.astype(np.float64)
    pad = w // 2
    kernel = np.ones(w, dtype=np.float64) / float(w)
    xpad = np.pad(x.astype(np.float64), (pad, pad), mode="reflect")
    return np.convolve(xpad, kernel, mode="valid")


def estimate_displacement_improved(
    I: np.ndarray,
    Q: np.ndarray,
    *,
    wavelength_m: float,
    offset_tracking_alpha: float = 0.01,
    phase_smooth_window: int = 21,
) -> dict[str, np.ndarray]:
    """Improved demodulation with drift-aware offset tracking + phase smoothing.

    - Tracks DC offsets per channel using EWMA.
    - Smooths unwrapped phase with a moving average.
    """
    I = np.asarray(I, dtype=np.float64)
    Q = np.asarray(Q, dtype=np.float64)

    I_off = _ewma(I, alpha=offset_tracking_alpha)
    Q_off = _ewma(Q, alpha=offset_tracking_alpha)

    Ic = I - I_off
    Qc = Q - Q_off

    phase = np.unwrap(np.arctan2(Qc, Ic))
    phase_s = _moving_average(phase, window=phase_smooth_window)

    x_hat = phase_s * (float(wavelength_m) / (4.0 * np.pi))
    return {"phase_hat": phase, "phase_hat_smooth": phase_s, "x_hat": x_hat}
