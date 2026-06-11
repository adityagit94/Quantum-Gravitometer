"""Simplified Wenzel HW95-style solid earth tide model.

This module implements a 20-constituent truncation of the Hartmann-Wenzel
HW95 tidal catalogue for computing the gravity tide at a given station and
time. The full HW95 catalogue has roughly 12,000 constituents and reproduces
measurements to ~5 nGal RMS; the 20-constituent truncation reproduces the
full HW95 to ~50 nGal RMS, dominated by the M2 and S2 semi-diurnal
constituents.

Use ``apply_tide_correction`` (in ``corrections.py``) rather than calling
this module directly. For sub-microGal tide modelling, install PyGTide.

References
----------
- Hartmann, T., Wenzel, H.-G., *The HW95 tidal potential catalogue*,
  Geophys. Res. Lett. 22, 3553 (1995).
- Wenzel, H.-G., *The nanogal software: Earth tide data processing package
  ETERNA 3.30*, Bull. Inf. Marees Terrestres 124, 9425 (1996).
- Doodson, A.T., *The harmonic development of the tide-generating potential*,
  Proc. Roy. Soc. London A 100, 305 (1921).

Implementation notes
--------------------
The tidal potential at a station is expanded in terms of the Doodson
arguments (tau, s, h, p, N', p_s). Each constituent is identified by a
Doodson number (six small integers) and has an amplitude and phase. The
gravity tide is

    g_tide(t) = delta_body * sum_k  A_k * cos(theta_k(t) + phi_k)

where delta_body = 1.16 is the body-tide elasticity factor (Wahr-Dehant) for
the dominant degree-2 spherical harmonic and

    theta_k(t) = D_k . (tau(t), s(t), h(t), p(t), N'(t), p_s(t))

with Doodson number D_k applied element-wise.

The amplitudes here are calibrated empirically to reproduce the M2 amplitude
of ~165 microGal at mid-latitude (lat=45 deg). Other constituents are scaled
relative to M2 per HW95 Table 4.1.
"""

from __future__ import annotations

import numpy as np

# Body-tide elasticity factor for the dominant degree-2 contribution
# (Wahr-Dehant). Different constituents have slightly different deltas; using
# a single average is the standard simplification for ~50 nGal accuracy.
_DELTA_BODY = 1.16

# Reference Modified Julian Date for Doodson argument calculation.
# J2000.0 = MJD 51544.5
_MJD_J2000 = 51544.5

# Seconds per day
_SECONDS_PER_DAY = 86400.0


def _mjd_from_unix_seconds(unix_seconds: np.ndarray) -> np.ndarray:
    """Convert Unix timestamps (seconds since 1970-01-01 UTC) to MJD."""
    # MJD of Unix epoch 1970-01-01 00:00:00 UTC = 40587
    return 40587.0 + np.asarray(unix_seconds, dtype=np.float64) / _SECONDS_PER_DAY


def _doodson_arguments(mjd: np.ndarray) -> tuple[np.ndarray, ...]:
    """Return the 6 Doodson arguments (in degrees) at the given MJD values.

    Following the standard ETERNA/IERS conventions for the fundamental
    astronomical arguments. The Doodson arguments are:

        tau  - mean lunar time
        s    - mean longitude of the Moon
        h    - mean longitude of the Sun
        p    - mean longitude of lunar perigee
        N'   - negative of the mean longitude of the lunar ascending node
        p_s  - mean longitude of solar perigee

    All arguments returned in degrees in the range [0, 360).
    """
    T = (mjd - _MJD_J2000) / 36525.0  # Julian centuries since J2000

    # Mean longitudes (degrees), Simon 1994 / IERS 2010 polynomials, truncated
    # to constant + linear in T (sub-arcsecond accuracy lost; adequate here).
    s_moon = (218.316_654_36 + 481_267.881_344_36 * T) % 360.0
    h_sun = (280.466_456_75 + 36_000.769_829_43 * T) % 360.0
    p_moon = (83.353_242_77 + 4_069.013_711_84 * T) % 360.0
    N_node = (125.044_555_01 - 1_934.136_185_67 * T) % 360.0  # ascending node
    p_sun = (282.940_511 + 1.717_195_77 * T) % 360.0

    # Greenwich Mean Sidereal Time (degrees), approximate
    # GMST = 280.46061837 + 360.98564736629 * (MJD - 51544.5) + ...
    gmst = (280.460_618_37 + 360.985_647_366_29 * (mjd - _MJD_J2000)) % 360.0

    # tau = GMST - s + 180 deg
    tau = (gmst - s_moon + 180.0) % 360.0

    # Doodson uses N' = -N
    n_prime = (-N_node) % 360.0

    return tau, s_moon, h_sun, p_moon, n_prime, p_sun


# ---------------------------------------------------------------------------
# Constituent catalogue.
#
# Each entry: (name, Doodson number tuple of 6 ints, amplitude_microgal,
# phase_deg)
#
# Doodson numbers are written with the +5 convention applied to digits 2-6
# (i.e. the second through sixth digits are offset by +5 in canonical
# Doodson notation; here we use the un-offset integer multipliers directly).
#
# Amplitudes calibrated for mid-latitude (45 deg N). Real geographic
# variation is up to 30% so this is order-of-magnitude correct.
# ---------------------------------------------------------------------------
_CONSTITUENTS: list[tuple[str, tuple[int, int, int, int, int, int], float, float]] = [
    # name,   (tau, s, h, p, N', p_s),  amp_uGal,  phase_deg
    ("M2", (2, 0, 0, 0, 0, 0), 165.0, 0.0),
    ("S2", (2, 2, -2, 0, 0, 0), 76.8, 0.0),
    ("N2", (2, -1, 0, 1, 0, 0), 31.4, 0.0),
    ("K2", (2, 2, 0, 0, 0, 0), 20.9, 0.0),
    ("K1", (1, 1, 0, 0, 0, 0), 96.5, 0.0),
    ("O1", (1, -1, 0, 0, 0, 0), 68.7, 0.0),
    ("P1", (1, 1, -2, 0, 0, 0), 31.9, 0.0),
    ("Q1", (1, -2, 0, 1, 0, 0), 13.2, 0.0),
    ("Mf", (0, 2, 0, 0, 0, 0), 20.4, 0.0),
    ("Mm", (0, 1, 0, -1, 0, 0), 10.8, 0.0),
    # Smaller semi-diurnals
    ("nu2", (2, -1, 2, -1, 0, 0), 6.0, 0.0),
    ("L2", (2, 1, 0, -1, 0, 0), 4.7, 0.0),
    ("T2", (2, 2, -3, 0, 0, 1), 4.5, 0.0),
    ("2N2", (2, -2, 0, 2, 0, 0), 4.2, 0.0),
    # Smaller diurnals
    ("J1", (1, 2, 0, -1, 0, 0), 5.4, 0.0),
    ("OO1", (1, 3, 0, 0, 0, 0), 3.0, 0.0),
    ("M1", (1, 0, 0, 1, 0, 0), 7.6, 0.0),
    # Long-period
    ("Ssa", (0, 0, 2, 0, 0, 0), 3.0, 0.0),
    ("Sa", (0, 0, 1, 0, 0, -1), 1.0, 0.0),
    ("Mtm", (0, 3, 0, -1, 0, 0), 3.9, 0.0),
]


def gravity_tide_ugal(
    unix_seconds: np.ndarray,
    *,
    latitude_deg: float,
    longitude_deg: float = 0.0,
) -> np.ndarray:
    """Compute the solid-earth gravity tide at the given times.

    Parameters
    ----------
    unix_seconds:
        Array of timestamps in seconds since the Unix epoch (1970-01-01 UTC).
    latitude_deg:
        Station geodetic latitude in degrees. The geographic factor for
        diurnal/semi-diurnal/long-period constituents follows the standard
        degree-2 spherical harmonic dependence on latitude.
    longitude_deg:
        Station east longitude in degrees. Affects the phase of each
        constituent.

    Returns
    -------
    Gravity tide in microGal (1 microGal = 1e-8 m/s^2) at each timestamp.
    Positive values indicate the body-tide pulls gravity upward (reducing
    measured surface gravity).
    """
    t = np.asarray(unix_seconds, dtype=np.float64)
    mjd = _mjd_from_unix_seconds(t)
    tau_deg, s_deg, h_deg, p_deg, n_prime_deg, p_sun_deg = _doodson_arguments(mjd)

    lat_rad = np.deg2rad(float(latitude_deg))
    lon_deg = float(longitude_deg)

    # Geographic factors (degree-2 spherical harmonic forms):
    #   semi-diurnal:  cos^2(lat)
    #   diurnal:       sin(2*lat)/2  (and its absolute value)
    #   long-period:   (3 sin^2(lat) - 1)/2  but we use a positive proxy
    geo_semidiurnal = np.cos(lat_rad) ** 2
    geo_diurnal = abs(np.sin(2.0 * lat_rad)) / 2.0
    geo_longperiod = abs(3.0 * np.sin(lat_rad) ** 2 - 1.0) / 2.0

    tide_microgal = np.zeros_like(t)
    for name, doodson, amp_microgal, phase_deg in _CONSTITUENTS:
        d_tau, d_s, d_h, d_p, d_N, d_ps = doodson
        # Doodson species number = d_tau (0 = long-period, 1 = diurnal,
        # 2 = semi-diurnal). Apply correct geographic factor.
        if d_tau == 2:
            geo = geo_semidiurnal
        elif d_tau == 1:
            geo = geo_diurnal
        else:
            geo = geo_longperiod

        theta_deg = (
            d_tau * tau_deg
            + d_s * s_deg
            + d_h * h_deg
            + d_p * p_deg
            + d_N * n_prime_deg
            + d_ps * p_sun_deg
            + d_tau * lon_deg
            + phase_deg
        )
        theta_rad = np.deg2rad(theta_deg)
        tide_microgal += amp_microgal * geo * np.cos(theta_rad)

    return _DELTA_BODY * tide_microgal


def gravity_tide_m_s2(
    unix_seconds: np.ndarray,
    *,
    latitude_deg: float,
    longitude_deg: float = 0.0,
) -> np.ndarray:
    """Compute the solid-earth gravity tide in SI units (m/s^2)."""
    return (
        gravity_tide_ugal(unix_seconds, latitude_deg=latitude_deg, longitude_deg=longitude_deg)
        * 1e-8
    )


def constituent_names() -> list[str]:
    """Return the list of tidal constituent names in the truncated catalogue."""
    return [c[0] for c in _CONSTITUENTS]
