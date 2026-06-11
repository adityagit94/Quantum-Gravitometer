"""Three-pulse Mach-Zehnder sensitivity function and vibration transfer function.

The sensitivity function g_s(t) of an atom interferometer relates a
time-dependent laser-phase perturbation delta_phi(t) to the resulting
interferometer phase shift:

    delta_Phi = int g_s(t) * delta_phi(t) dt

For a Mach-Zehnder pi/2 - pi - pi/2 sequence with free-evolution time T and
infinitesimally short pulses, the canonical result (Cheinet 2008) is::

    g_s(t) = -1     for  0 < t < T
    g_s(t) = +1     for  T < t < 2T
    g_s(t) =  0     elsewhere

When the laser-phase perturbation comes from mirror vibration via
phi(t) = k_eff * z(t), the frequency-domain transfer function from
acceleration PSD S_a(f) to interferometer phase variance is

    sigma_phi^2 = int |H(2 pi f)|^2 * S_a(f) df

with (instantaneous-pulse limit)

    |H(2 pi f)|^2 = 16 sin^4(pi f T) / (2 pi f)^2

The resulting equivalent gravity noise is sigma_g = sigma_phi / (k_eff T^2).

This module provides the time-domain g_s(t), the frequency-domain
|H(2 pi f)|^2, and a broadband integrator that takes an acceleration PSD and
returns the equivalent gravity noise.

References
----------
- Cheinet, P. et al., *Measurement of the sensitivity function in a time-domain
  atomic interferometer*, IEEE Trans. Instrum. Meas. 57, 1141 (2008),
  arXiv:physics/0510197.
- Le Gouet, J. et al., *Limits to the sensitivity of a low noise compact atomic
  gravimeter*, Appl. Phys. B 92, 133 (2008).
- Peterson, J., *Observations and modeling of seismic background noise*,
  USGS OFR 93-322 (1993).
"""

from __future__ import annotations

import numpy as np

from qgrav.physics._seismic_models import NHNM_PSD, NLNM_PSD, interpolate_psd

# NumPy 2.0 renamed trapz -> trapezoid. Stay compatible with both.
_trapezoid = getattr(np, "trapezoid", None) or np.trapz  # type: ignore[attr-defined]


def sensitivity_function_time_domain(
    t: np.ndarray,
    *,
    interferometer_time_s: float,
    pulse_duration_s: float = 0.0,
) -> np.ndarray:
    """Three-pulse Mach-Zehnder sensitivity function g_s(t).

    Origin convention: the first pi/2 pulse is centred at t = 0 and the third
    pi/2 pulse is centred at t = 2T, where T = ``interferometer_time_s``.

    In the instantaneous-pulse limit (``pulse_duration_s = 0``):

        g_s(t) = -1   for  0  < t < T
        g_s(t) = +1   for  T  < t < 2T
        g_s(t) =  0   elsewhere

    For finite pulse duration tau, the function ramps linearly through each
    pulse so that g_s is continuous (Cheinet 2008, eqs. 7-10). The central pi
    pulse has duration 2*tau and is centred at t = T.

    Parameters
    ----------
    t:
        Times in seconds at which to evaluate g_s.
    interferometer_time_s:
        Free-evolution time T between pulses.
    pulse_duration_s:
        Duration of each pi/2 pulse (tau). The central pi pulse has duration
        2*tau. Defaults to 0 (instantaneous-pulse limit).

    Returns
    -------
    Array of g_s(t) values with the same shape as ``t``.
    """
    t = np.asarray(t, dtype=float)
    T = float(interferometer_time_s)
    tau = float(pulse_duration_s)
    if T <= 0:
        raise ValueError("interferometer_time_s must be positive")
    if tau < 0:
        raise ValueError("pulse_duration_s must be non-negative")

    out = np.zeros_like(t)

    if tau == 0.0:
        # Instantaneous-pulse limit.
        in_first = (t > 0.0) & (t < T)
        in_second = (t > T) & (t < 2.0 * T)
        out[in_first] = -1.0
        out[in_second] = +1.0
        return out

    # Finite-pulse Cheinet form. Pulse centres are at 0, T, 2T with durations
    # tau, 2*tau, tau respectively. The piecewise function is:
    #   t in [-tau/2, +tau/2]:        ramp -sin(pi (t + tau/2) / tau)  (first pi/2)
    #     -> approximation: ramp linearly from 0 to -1
    #   t in [tau/2, T - tau]:        constant -1
    #   t in [T - tau, T + tau]:      central pi pulse, ramp from -1 to +1
    #   t in [T + tau, 2T - tau/2]:   constant +1
    #   t in [2T - tau/2, 2T + tau/2]: ramp from +1 to 0
    # Outside: 0.
    p1_start, p1_end = -tau / 2.0, tau / 2.0
    p2_start, p2_end = T - tau, T + tau
    p3_start, p3_end = 2.0 * T - tau / 2.0, 2.0 * T + tau / 2.0

    # First pulse ramp 0 -> -1
    mask1 = (t >= p1_start) & (t <= p1_end)
    out[mask1] = -(t[mask1] - p1_start) / (p1_end - p1_start)

    # First flat segment: -1
    mask_flat1 = (t > p1_end) & (t < p2_start)
    out[mask_flat1] = -1.0

    # Central pulse ramp -1 -> +1
    mask2 = (t >= p2_start) & (t <= p2_end)
    out[mask2] = -1.0 + 2.0 * (t[mask2] - p2_start) / (p2_end - p2_start)

    # Second flat segment: +1
    mask_flat2 = (t > p2_end) & (t < p3_start)
    out[mask_flat2] = +1.0

    # Third pulse ramp +1 -> 0
    mask3 = (t >= p3_start) & (t <= p3_end)
    out[mask3] = 1.0 - (t[mask3] - p3_start) / (p3_end - p3_start)

    return out


def transfer_function_vibration(
    f_hz: np.ndarray,
    *,
    interferometer_time_s: float,
    pulse_duration_s: float = 0.0,
) -> np.ndarray:
    """Laser-phase-noise transfer function squared |G(2 pi f)|^2.

    This is the squared magnitude of the Fourier transform of the
    time-domain sensitivity function g(t) (-1 on [0,T], +1 on [T,2T]):

        |G(2 pi f)|^2 = 16 sin^4(pi f T) / (2 pi f)^2

    Use this when the input noise PSD is a *laser phase* PSD in rad^2/Hz;
    the output phase variance is

        sigma_phi^2 = int |G(2 pi f)|^2 S_phi(f) df

    For mirror vibration (acceleration PSD) input, use
    :func:`acceleration_to_phase_transfer_function_sq` instead, which
    differs by a factor (k_eff / (2 pi f))^2.

    The transfer function has notches at f = n/T for n = 1, 2, 3, ... and
    rolls off as 1/f^2 above 1/T.

    For finite pulse duration tau, a sinc^2 factor multiplies the
    instantaneous-pulse expression:

        |G_tau(2 pi f)|^2 = |G_0(2 pi f)|^2 * sinc^2(pi f tau)

    where sinc(x) = sin(x)/x.

    Parameters
    ----------
    f_hz:
        Frequencies at which to evaluate, in Hz. f = 0 returns 0.
    interferometer_time_s:
        Free-evolution time T.
    pulse_duration_s:
        Pulse duration tau (default 0).

    Returns
    -------
    Array of |G|^2 values; multiply by laser-phase PSD (rad^2/Hz) and
    integrate over df to obtain phase variance in rad^2.
    """
    f = np.asarray(f_hz, dtype=float)
    T = float(interferometer_time_s)
    tau = float(pulse_duration_s)
    if T <= 0:
        raise ValueError("interferometer_time_s must be positive")

    out = np.zeros_like(f)
    nonzero = f != 0.0
    f_nz = f[nonzero]
    omega = 2.0 * np.pi * f_nz
    base = 16.0 * np.sin(np.pi * f_nz * T) ** 4 / (omega**2)
    if tau > 0:
        sinc_factor = np.where(
            f_nz == 0.0,
            1.0,
            (np.sin(np.pi * f_nz * tau) / (np.pi * f_nz * tau)) ** 2,
        )
        base = base * sinc_factor
    out[nonzero] = base
    return out


def acceleration_to_phase_transfer_function_sq(
    f_hz: np.ndarray,
    *,
    interferometer_time_s: float,
    pulse_duration_s: float = 0.0,
    k_eff_rad_per_m: float,
) -> np.ndarray:
    """Mod-squared transfer function from acceleration PSD to phase variance.

    Integrating an acceleration PSD S_a(f) in (m/s^2)^2/Hz against this
    function yields the interferometer phase variance:

        sigma_phi^2 = int |H_a(2 pi f)|^2 S_a(f) df

    with

        |H_a(2 pi f)|^2 = 16 k_eff^2 sin^4(pi f T) / (2 pi f)^4

    Equivalently, the acceleration-to-equivalent-gravity transfer function
    squared is |H_a|^2 / (k_eff^2 T^4) = 16 sin^4(pi f T) / [(2 pi f)^4 T^4].

    Derivation: the second-difference operator [1, -2, 1] applied to z(0),
    z(T), z(2T) has discrete-frequency response |H_disc|^2 = 16 sin^4(pi f T).
    Converting displacement PSD S_z = S_a / (2 pi f)^4 and multiplying by
    k_eff^2 gives the formula above.
    """
    f = np.asarray(f_hz, dtype=float)
    T = float(interferometer_time_s)
    if T <= 0:
        raise ValueError("interferometer_time_s must be positive")
    if k_eff_rad_per_m <= 0:
        raise ValueError("k_eff_rad_per_m must be positive")
    out = np.zeros_like(f)
    nz = f != 0.0
    f_nz = f[nz]
    omega = 2.0 * np.pi * f_nz
    base = 16.0 * (k_eff_rad_per_m**2) * np.sin(np.pi * f_nz * T) ** 4 / (omega**4)
    if pulse_duration_s > 0:
        sinc_sq = (np.sin(np.pi * f_nz * pulse_duration_s) / (np.pi * f_nz * pulse_duration_s)) ** 2
        base = base * sinc_sq
    out[nz] = base
    return out


def integrate_vibration_noise(
    psd_acceleration: np.ndarray,
    f_hz: np.ndarray,
    *,
    interferometer_time_s: float,
    pulse_duration_s: float = 0.0,
    k_eff_rad_per_m: float,
) -> dict[str, float]:
    """Integrate an acceleration PSD against the vibration transfer function.

    Computes

        sigma_phi^2 = int_0^infty |H(2 pi f)|^2 * S_a(f) df

    via trapezoidal integration on the supplied frequency grid, and converts to
    equivalent gravity noise

        sigma_g = sigma_phi / (k_eff * T^2)

    Parameters
    ----------
    psd_acceleration:
        Acceleration PSD values S_a(f) in (m/s^2)^2 / Hz.
    f_hz:
        Frequency grid (must be sorted ascending, same length as
        ``psd_acceleration``).
    interferometer_time_s:
        T parameter.
    pulse_duration_s:
        Pulse duration tau (default 0).
    k_eff_rad_per_m:
        Effective wave vector for the Raman transition.

    Returns
    -------
    dict with keys ``sigma_phi_rad``, ``sigma_g_m_s2``, ``sigma_g_ugal``.
    """
    f = np.asarray(f_hz, dtype=float)
    psd = np.asarray(psd_acceleration, dtype=float)
    if f.shape != psd.shape:
        raise ValueError("f_hz and psd_acceleration must have the same shape")
    if np.any(np.diff(f) <= 0):
        raise ValueError("f_hz must be strictly increasing")
    if k_eff_rad_per_m <= 0:
        raise ValueError("k_eff_rad_per_m must be positive")

    # Acceleration-to-phase transfer function squared:
    #     |H_a(2 pi f)|^2 = 16 k_eff^2 sin^4(pi f T) / (2 pi f)^4
    # so that  sigma_phi^2 = int |H_a|^2 S_a df.
    # The equivalent gravity noise is sigma_g = sigma_phi / (k_eff * T^2).
    H_a_sq = acceleration_to_phase_transfer_function_sq(
        f,
        interferometer_time_s=interferometer_time_s,
        pulse_duration_s=pulse_duration_s,
        k_eff_rad_per_m=k_eff_rad_per_m,
    )
    integrand = H_a_sq * psd
    sigma_phi_sq = float(_trapezoid(integrand, f))
    sigma_phi = float(np.sqrt(max(sigma_phi_sq, 0.0)))
    T = interferometer_time_s
    sigma_g = sigma_phi / (k_eff_rad_per_m * (T**2))
    return {
        "sigma_phi_rad": sigma_phi,
        "sigma_g_m_s2": sigma_g,
        "sigma_g_ugal": sigma_g * 1e8,
    }


__all__ = [
    "sensitivity_function_time_domain",
    "transfer_function_vibration",
    "acceleration_to_phase_transfer_function_sq",
    "integrate_vibration_noise",
    "NLNM_PSD",
    "NHNM_PSD",
    "interpolate_psd",
]
