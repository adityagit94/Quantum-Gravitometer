from __future__ import annotations

import numpy as np


def estimate_displacement_baseline(
    I: np.ndarray, Q: np.ndarray, *, wavelength_m: float
) -> dict[str, np.ndarray]:
    """Baseline quadrature demodulation.

    1) subtract global means (assumes constant offsets)
    2) phase = unwrap(atan2(Qc, Ic))
    3) displacement = phase * λ / (4π)  (Michelson model)
    """
    I = np.asarray(I, dtype=np.float64)
    Q = np.asarray(Q, dtype=np.float64)
    Ic = I - np.mean(I)
    Qc = Q - np.mean(Q)
    phase = np.unwrap(np.arctan2(Qc, Ic))
    x_hat = phase * (float(wavelength_m) / (4.0 * np.pi))
    return {"phase_hat": phase, "x_hat": x_hat}
