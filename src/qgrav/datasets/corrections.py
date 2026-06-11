"""Real-data corrections for gravimetry time-series.

Provides:

- :func:`detect_igets_level` — heuristic for IGETS data product level (1, 2, 3)
- :func:`apply_tide_correction` — solid earth tide subtraction (PyGTide
  preferred, simplified HW95 fallback)
- :func:`apply_pressure_correction` — atmospheric pressure admittance
- :func:`apply_polar_motion_correction` — pole tide from IERS x_p/y_p
- :func:`apply_ocean_loading_correction` — ocean tidal loading from
  per-constituent BLQ amplitudes/phases

References
----------
- Voigt, C. et al., *International Geodynamics and Earth Tide Service (IGETS)
  Data Centre*, GFZ Potsdam (2016), https://igets.gfz.de
- Crossley, D. et al., *Effective barometric admittance and gravity
  residuals*, Phys. Earth Planet. Inter. 90, 221 (1995).
- Wenzel, H.-G., *The nanogal software: Earth tide data processing package
  ETERNA 3.30*, Bull. Inf. Marees Terrestres 124, 9425 (1996).
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

import numpy as np

from qgrav.datasets._tides_hw95 import gravity_tide_m_s2

logger = logging.getLogger(__name__)


def _try_import_pygtide():
    """Best-effort import of PyGTide. Returns the module or ``None``."""
    try:
        import pygtide

        return pygtide
    except Exception:
        return None


def detect_igets_level(data: dict[str, Any]) -> int:
    """Heuristic detection of the IGETS data product level (1, 2, or 3).

    Uses sample rate as the dominant cue:

        - sample rate ~ 1 Hz  -> Level 1 (raw 1-second gravimeter output)
        - sample rate ~ 1/60 Hz (1 minute) -> Level 2
        - sample rate ~ 1/3600 Hz (1 hour) -> Level 3

    If the sample rate is ambiguous, returns 1 (conservative — apply
    corrections).

    Parameters
    ----------
    data:
        Dict returned by ``load_real_gravity_dataset``. Expected to contain
        a ``sample_rate_hz`` key.
    """
    fs = float(data.get("sample_rate_hz", 0.0) or 0.0)
    if fs <= 0:
        return 1  # conservative
    if fs > 0.5:
        return 1  # 1 Hz or faster
    if fs > 0.005:
        return 2  # ~ 1/60 Hz
    return 3  # hourly or coarser


def apply_tide_correction(
    timestamps: np.ndarray,
    values: np.ndarray,
    *,
    longitude_deg: float,
    latitude_deg: float,
    height_m: float = 0.0,
    backend: str = "auto",
) -> dict[str, Any]:
    """Subtract solid-earth tide from a gravity residual series.

    Parameters
    ----------
    timestamps:
        Unix seconds (UTC) for each sample.
    values:
        Gravity residual values in m/s^2.
    longitude_deg, latitude_deg, height_m:
        Station coordinates.
    backend:
        One of:

        - ``"pygtide"`` — require PyGTide; raise if not installed.
        - ``"internal_hw95"`` — use the simplified internal Wenzel HW95 model.
        - ``"auto"`` (default) — try PyGTide, fall back to ``internal_hw95``
          with a logger warning.

    Returns
    -------
    dict with keys:

        ``corrected``
            ``values - tide`` (same shape and units as ``values``).
        ``tide_subtracted``
            The subtracted tide series (m/s^2).
        ``backend_used``
            ``"pygtide"`` or ``"internal_hw95"``.
        ``rms_subtracted_ugal``
            RMS of the subtracted tide in microGal.
    """
    t = np.asarray(timestamps, dtype=np.float64)
    v = np.asarray(values, dtype=np.float64)
    if t.shape != v.shape:
        raise ValueError("timestamps and values must have the same shape")
    if backend not in {"pygtide", "internal_hw95", "auto"}:
        raise ValueError(f"unknown tide backend: {backend!r}")

    used_backend = backend
    if backend in {"pygtide", "auto"}:
        pygtide = _try_import_pygtide()
        if pygtide is None:
            if backend == "pygtide":
                raise ImportError(
                    "PyGTide backend requested but the package is not installed. "
                    "Install with `pip install pygtide`, or use "
                    "backend='internal_hw95'."
                )
            logger.warning(
                "PyGTide not available; falling back to internal HW95 tide model. "
                "Expect ~50 nGal RMS error vs full HW95. Install PyGTide for "
                "sub-microGal tide modelling."
            )
            used_backend = "internal_hw95"
        else:
            tide = _compute_tide_pygtide(
                pygtide,
                t,
                latitude_deg=latitude_deg,
                longitude_deg=longitude_deg,
                height_m=height_m,
            )
            used_backend = "pygtide"
            corrected = v - tide
            rms_ugal = float(np.sqrt(np.mean(tide**2)) * 1e8)
            return {
                "corrected": corrected,
                "tide_subtracted": tide,
                "backend_used": used_backend,
                "rms_subtracted_ugal": rms_ugal,
            }

    # internal_hw95 path
    tide = gravity_tide_m_s2(t, latitude_deg=latitude_deg, longitude_deg=longitude_deg)
    corrected = v - tide
    if tide.size > 0:
        rms_ugal = float(np.sqrt(np.mean(tide**2)) * 1e8)
    else:
        rms_ugal = float("nan")
    return {
        "corrected": corrected,
        "tide_subtracted": tide,
        "backend_used": used_backend,
        "rms_subtracted_ugal": rms_ugal,
    }


def _compute_tide_pygtide(
    pygtide_mod: Any,
    timestamps: np.ndarray,
    *,
    latitude_deg: float,
    longitude_deg: float,
    height_m: float,
) -> np.ndarray:
    """Call PyGTide on the requested timestamps and return tide in m/s^2.

    PyGTide takes a start datetime, sample interval, and number of samples,
    so we resample its output onto the requested timestamps via linear
    interpolation (PyGTide's output is smooth on minute scales).
    """
    import datetime as _dt

    pt = pygtide_mod.pygtide()
    t = np.asarray(timestamps, dtype=np.float64)
    if t.size == 0:
        return np.zeros(0)
    # Use a uniform 60-second grid bracketing the input
    t0 = float(t[0])
    t1 = float(t[-1])
    duration_s = max(t1 - t0, 60.0)
    samples_per = 60.0  # seconds per sample
    # Naive-UTC datetime (what PyGTide expects); utcfromtimestamp is deprecated.
    start_dt = _dt.datetime.fromtimestamp(t0, _dt.UTC).replace(tzinfo=None)
    pt.predict(
        latitude=latitude_deg,
        longitude=longitude_deg,
        height=height_m,
        start_datetime=start_dt,
        duration=int(np.ceil(duration_s / 3600.0)) + 1,  # PyGTide takes hours
        samplerate=samples_per,
    )
    df = pt.results()
    # df has 'UTC' and 'Signal [nm/s**2]' columns (or similar)
    if "Signal [nm/s**2]" in df.columns:
        signal_col = "Signal [nm/s**2]"
    else:
        # Best effort: find column with 'Signal' in the name
        candidates = [c for c in df.columns if "Signal" in c]
        if not candidates:
            raise RuntimeError("PyGTide output has no 'Signal' column")
        signal_col = candidates[0]
    tide_nm_s2 = df[signal_col].to_numpy()
    grid_unix = df["UTC"].astype("int64").to_numpy() / 1e9
    tide_m_s2 = tide_nm_s2 * 1e-9
    # Linear interpolate onto requested timestamps
    return np.interp(t, grid_unix, tide_m_s2)


def apply_pressure_correction(
    timestamps: np.ndarray,
    gravity: np.ndarray,
    pressure: np.ndarray,
    *,
    admittance_nm_s2_per_hpa: float = -3.0,
    reference_pressure_hpa: float | None = None,
) -> np.ndarray:
    """Apply linear barometric admittance correction.

    The standard correction (Crossley 1995) is::

        g_corrected = g_observed - admittance * (P - P_ref)

    where admittance is typically -3 nm/s^2/hPa (negative: high pressure
    decreases measured gravity).

    Parameters
    ----------
    timestamps:
        Time array (Unix seconds), used only for shape verification.
    gravity:
        Observed gravity in m/s^2.
    pressure:
        Co-located atmospheric pressure in hPa.
    admittance_nm_s2_per_hpa:
        Local admittance value. Default -3.0 per Crossley 1995. Sign
        convention: gravity decreases when pressure increases.
    reference_pressure_hpa:
        Reference pressure. If ``None``, the mean of the input pressure is
        used.

    Returns
    -------
    Corrected gravity in m/s^2.
    """
    t = np.asarray(timestamps, dtype=np.float64)
    g = np.asarray(gravity, dtype=np.float64)
    p = np.asarray(pressure, dtype=np.float64)
    if g.shape != p.shape or g.shape != t.shape:
        raise ValueError("timestamps, gravity, and pressure must share shape")
    p_ref = (
        float(reference_pressure_hpa) if reference_pressure_hpa is not None else float(np.mean(p))
    )
    admittance_m_s2_per_hpa = admittance_nm_s2_per_hpa * 1e-9
    correction = admittance_m_s2_per_hpa * (p - p_ref)
    return g - correction


def apply_polar_motion_correction(
    g: np.ndarray,
    latitude_deg: float,
    longitude_deg: float,
    xp_arcsec: np.ndarray | float,
    yp_arcsec: np.ndarray | float,
    *,
    gravimetric_factor: float = 1.164,
) -> np.ndarray:
    """Apply the polar-motion (pole tide) gravity correction.

    Physics (IERS Conventions 2010, ch. 7; IAGBN standard)::

        delta_g = -delta * omega^2 * R * sin(2*phi) * (x_p*cos(lam) - y_p*sin(lam))

    with Earth rotation rate ``omega = 7.292115e-5 rad/s``, mean radius
    ``R = 6.371e6 m``, gravimetric factor ``delta = 1.164``, station latitude
    ``phi`` / east longitude ``lam``, and pole coordinates ``x_p``/``y_p``
    converted from arcseconds to radians.

    Sign convention (same as :func:`apply_pressure_correction`):
    **corrected = observed - effect**, i.e. the returned series is
    ``g - delta_g``.

    Parameters
    ----------
    g:
        Observed gravity (residual) series in m/s^2.
    latitude_deg, longitude_deg:
        Station geodetic latitude and east longitude in degrees.
    xp_arcsec, yp_arcsec:
        Pole coordinates in arcseconds: either scalars (single epoch,
        adequate for series much shorter than the ~433-day Chandler period)
        or arrays aligned sample-by-sample with ``g``. Obtain them from the
        IERS EOP 14 C04 series at
        https://datacenter.iers.org/data/latestVersion/finals.all.iau2000.txt
        (or https://hpiers.obspm.fr/iers/eop/eopc04/) - columns ``x_pole``
        and ``y_pole`` (arcsec).

    Returns
    -------
    Corrected gravity in m/s^2 (same shape as ``g``).
    """
    g_arr = np.asarray(g, dtype=np.float64)
    xp = np.asarray(xp_arcsec, dtype=np.float64)
    yp = np.asarray(yp_arcsec, dtype=np.float64)
    if xp.ndim > 0 and xp.shape != g_arr.shape:
        raise ValueError("array xp_arcsec must match the shape of g")
    if yp.ndim > 0 and yp.shape != g_arr.shape:
        raise ValueError("array yp_arcsec must match the shape of g")

    omega_rad_s = 7.292115e-5  # Earth rotation rate (rad/s)
    radius_m = 6.371e6  # mean Earth radius (m)
    arcsec_to_rad = np.deg2rad(1.0 / 3600.0)

    phi = np.deg2rad(float(latitude_deg))
    lam = np.deg2rad(float(longitude_deg))
    delta_g = (
        -float(gravimetric_factor)
        * omega_rad_s**2
        * radius_m
        * np.sin(2.0 * phi)
        * (xp * arcsec_to_rad * np.cos(lam) - yp * arcsec_to_rad * np.sin(lam))
    )
    return g_arr - delta_g


# Ocean-loading synthesis reuses the regression-locked HW95 astronomical
# machinery (imported, never edited): Doodson arguments chi(t) at Greenwich.
_OCEAN_LOADING_SUPPORTED = (
    "M2",
    "S2",
    "N2",
    "K2",
    "K1",
    "O1",
    "P1",
    "Q1",
    "Mf",
    "Mm",
    "Ssa",
)


def _constituent_argument_deg(name: str, times_unix_s: np.ndarray) -> np.ndarray:
    """Astronomical argument chi(t) in degrees at Greenwich for a constituent."""
    from qgrav.datasets._tides_hw95 import (
        _CONSTITUENTS,
        _doodson_arguments,
        _mjd_from_unix_seconds,
    )

    doodson = {c[0]: c[1] for c in _CONSTITUENTS}[name]
    mjd = _mjd_from_unix_seconds(np.asarray(times_unix_s, dtype=np.float64))
    args_deg = _doodson_arguments(mjd)
    chi = np.zeros_like(mjd)
    for mult, arg in zip(doodson, args_deg, strict=True):
        chi = chi + mult * arg
    return chi


def apply_ocean_loading_correction(
    times_unix_s: np.ndarray,
    g: np.ndarray,
    constituents: Sequence[dict],
) -> np.ndarray:
    """Apply an ocean tidal loading correction from per-constituent values.

    The user supplies amplitude and local phase per constituent - the values
    straight out of a BLQ file from the Onsala free-ocean-loading provider
    (http://holt.oso.chalmers.se/loading/): request the *gravity* loading
    for your station; in the returned BLQ block the **first row** holds the
    amplitudes (m/s^2 there, commonly quoted as nm/s^2 - check the header)
    and the **fourth row** the local phase lags in degrees, one column per
    constituent. BLQ gravity amplitudes are positive-down by convention.

    qgrav synthesizes the loading series with the same astronomical-argument
    machinery the solid-earth tide module uses::

        delta_g(t) = sum_i A_i * cos(chi_i(t) - phi_i)

    where ``chi_i(t)`` is the constituent's Doodson argument at Greenwich
    and ``phi_i`` the supplied local phase lag.

    Sign convention (same as :func:`apply_pressure_correction`):
    **corrected = observed - effect**, i.e. ``g - delta_g``.

    Parameters
    ----------
    times_unix_s:
        Timestamps (Unix seconds, UTC) aligned with ``g``.
    g:
        Observed gravity (residual) series in m/s^2.
    constituents:
        Sequence of dicts ``{"name": "M2", "amplitude_nm_s2": float,
        "phase_deg": float}``. Supported names:
        M2, S2, N2, K2, K1, O1, P1, Q1, Mf, Mm, Ssa.

    Returns
    -------
    Corrected gravity in m/s^2 (same shape as ``g``).
    """
    t = np.asarray(times_unix_s, dtype=np.float64)
    g_arr = np.asarray(g, dtype=np.float64)
    if t.shape != g_arr.shape:
        raise ValueError("times_unix_s and g must have the same shape")

    delta_g = np.zeros_like(g_arr)
    for entry in constituents:
        name = str(entry["name"])
        if name not in _OCEAN_LOADING_SUPPORTED:
            raise ValueError(
                f"unknown ocean-loading constituent {name!r}; supported: "
                + ", ".join(_OCEAN_LOADING_SUPPORTED)
            )
        amplitude_m_s2 = float(entry["amplitude_nm_s2"]) * 1e-9
        phase_rad = np.deg2rad(float(entry["phase_deg"]))
        chi_rad = np.deg2rad(_constituent_argument_deg(name, t))
        delta_g = delta_g + amplitude_m_s2 * np.cos(chi_rad - phase_rad)
    return g_arr - delta_g


__all__ = [
    "detect_igets_level",
    "apply_tide_correction",
    "apply_pressure_correction",
    "apply_polar_motion_correction",
    "apply_ocean_loading_correction",
]
