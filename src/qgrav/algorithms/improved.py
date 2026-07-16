from __future__ import annotations

import numpy as np
from scipy.signal import lfilter


def _ewma(x: np.ndarray, alpha: float) -> np.ndarray:
    a = float(alpha)
    x64 = np.asarray(x, dtype=np.float64)
    # Single-pole IIR y[i] = a*x[i] + (1-a)*y[i-1] with y[0] = x[0]; the
    # initial condition zi = (1-a)*x[0] makes lfilter start at y[0] = x[0].
    y, _ = lfilter([a], [1.0, -(1.0 - a)], x64, zi=np.array([(1.0 - a) * x64[0]]))
    return np.asarray(y, dtype=np.float64)


def _moving_average(x: np.ndarray, window: int) -> np.ndarray:
    w = int(window)
    if w <= 1:
        return x.astype(np.float64)
    # Pad (w-1)//2 left and w//2 right so the output length equals len(x) for
    # both odd and even windows (symmetric w//2 padding yields n+1 samples
    # when w is even).
    pad_left = (w - 1) // 2
    pad_right = w // 2
    kernel = np.ones(w, dtype=np.float64) / float(w)
    xpad = np.pad(x.astype(np.float64), (pad_left, pad_right), mode="reflect")
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
