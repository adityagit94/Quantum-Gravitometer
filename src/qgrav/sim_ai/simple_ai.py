from __future__ import annotations

import numpy as np


def phase_mach_zehnder(k_eff: float, acceleration: float, T: float) -> float:
    """Idealized phase for a 3-pulse light‑pulse atom interferometer (minimal baseline).

    Common simplified form:
        phi = k_eff * a * T^2

    This is used here as an auditable baseline. Higher fidelity models can replace this
    module later, while preserving the same pipeline interfaces.

    Args:
        k_eff: Effective wavevector (1/m)
        acceleration: Acceleration along sensitive axis (m/s^2)
        T: Pulse separation time (s)

    Returns:
        Phase shift (radians)
    """
    return float(k_eff * acceleration * (T**2))


def simulate_phase_timeseries(
    *,
    k_eff: float,
    T: float,
    a_mean: float,
    sample_rate_hz: float,
    duration_s: float,
    a_noise_std: float = 0.0,
    seed: int | None = None,
) -> dict[str, np.ndarray]:
    """Generate a simple phase time series from acceleration noise.

    a(t) = a_mean + N(0, a_noise_std)
    phi(t) = k_eff * a(t) * T^2
    """
    rng = np.random.default_rng(seed)
    n = int(round(duration_s * sample_rate_hz))
    t = np.arange(n, dtype=np.float64) / float(sample_rate_hz)
    a = np.full(n, float(a_mean), dtype=np.float64)
    if a_noise_std > 0:
        a = a + rng.normal(0.0, float(a_noise_std), size=n)
    phi = (float(k_eff) * (float(T) ** 2)) * a
    return {"t": t, "a": a, "phi": phi}
