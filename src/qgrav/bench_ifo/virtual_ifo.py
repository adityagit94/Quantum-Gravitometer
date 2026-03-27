from __future__ import annotations

import numpy as np

def _random_walk(rng: np.random.Generator, n: int, step_std: float) -> np.ndarray:
    steps = rng.normal(0.0, step_std, size=n)
    return np.cumsum(steps)

def generate_virtual_ifo(
    *,
    wavelength_m: float,
    sample_rate_hz: float,
    duration_s: float,
    displacement_sines: list[dict],
    measurement_noise_std: float,
    amplitude: float = 1.0,
    dc_offset: float = 0.0,
    offset_drift_std_per_s: float = 0.0,
    amplitude_drift_std_per_s: float = 0.0,
    seed: int | None = None,
) -> dict[str, np.ndarray]:
    """Generate virtual quadrature interferometer channels (I/Q) with truth displacement.

    Truth displacement:
        x_true(t) = Σ A_i sin(2π f_i t + phase_i)

    Michelson phase model (path difference 2x):
        phi(t) = 2π*(2x)/λ = 4π x / λ

    Quadrature channels:
        I(t) = offset_I(t) + amp(t) * cos(phi(t)) + noise
        Q(t) = offset_Q(t) + amp(t) * sin(phi(t)) + noise

    Offsets and amplitude can drift via random walk to simulate slow thermal/electronic drift.
    """
    rng = np.random.default_rng(seed)
    n = int(round(duration_s * sample_rate_hz))
    t = np.arange(n, dtype=np.float64) / float(sample_rate_hz)

    x_true = np.zeros(n, dtype=np.float64)
    for comp in displacement_sines:
        A = float(comp.get("amplitude_m", 0.0))
        f = float(comp.get("freq_hz", 0.0))
        ph = float(comp.get("phase_rad", 0.0))
        x_true += A * np.sin(2.0 * np.pi * f * t + ph)

    phi_true = (4.0 * np.pi / float(wavelength_m)) * x_true

    offset_rw = _random_walk(rng, n, step_std=float(offset_drift_std_per_s) / float(sample_rate_hz))
    amp_rw = _random_walk(rng, n, step_std=float(amplitude_drift_std_per_s) / float(sample_rate_hz))

    offset_I = float(dc_offset) + offset_rw
    offset_Q = float(dc_offset) - offset_rw  # anti-correlated drift

    amp_t = float(amplitude) * (1.0 + amp_rw)

    I_true = offset_I + amp_t * np.cos(phi_true)
    Q_true = offset_Q + amp_t * np.sin(phi_true)

    I_meas = I_true + rng.normal(0.0, float(measurement_noise_std), size=n)
    Q_meas = Q_true + rng.normal(0.0, float(measurement_noise_std), size=n)

    return {
        "t": t,
        "x_true": x_true,
        "phi_true": phi_true,
        "I_true": I_true,
        "Q_true": Q_true,
        "I_meas": I_meas,
        "Q_meas": Q_meas,
    }
