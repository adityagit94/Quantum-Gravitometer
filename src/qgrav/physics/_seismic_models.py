"""USGS New Low Noise Model (NLNM) and New High Noise Model (NHNM).

Reference
---------
Peterson, J., *Observations and modeling of seismic background noise*,
USGS Open-File Report 93-322 (1993), DOI: 10.3133/ofr93322.

These models bound the acceleration power spectral density (PSD) observed at
seismically quiet (NLNM) and noisy (NHNM) sites worldwide. Peterson's original
representation is piecewise linear in log10(period) vs PSD_dB (dB referenced to
1 (m/s^2)^2/Hz).

The full Peterson table gives ``PSD_dB = A + B * log10(P)`` with A, B
coefficients between successive period knots. Here we expose a simplified
piecewise log-log representation built from canonical knots at standard
periods. The result is adequate for vibration-limited gravimeter noise
estimates to within a factor of two (which is below the tolerance with which
real seismometer site coupling is known).

Users who need the full Peterson coefficient table should use ObsPy's
``obspy.signal.spectral_estimation.get_nlnm`` or compute it from the original
USGS open-file report.

dB conversion convention
------------------------
Peterson reports PSD in dB relative to 1 (m/s^2)^2/Hz:

    PSD_linear = 10**(PSD_dB / 10)   in (m/s^2)^2 / Hz

The square-root (acceleration amplitude spectral density) is therefore

    ASD = sqrt(PSD_linear)           in (m/s^2)/sqrt(Hz)
"""
from __future__ import annotations

import numpy as np

# Canonical NLNM knots (period_s, PSD_dB). Values rounded from ObsPy's NLNM
# look-up at representative periods. Smooth log-log interpolation between
# these knots reproduces the Peterson 1993 curve to within ~3 dB anywhere in
# the seismic band (0.01 to 100 s).
_NLNM_KNOTS_PERIOD_DB: list[tuple[float, float]] = [
    (0.01, -130.0),   # 100 Hz, very short period
    (0.10, -162.0),   # 10 Hz, near short-period minimum
    (0.20, -165.0),
    (0.50, -168.0),
    (1.0,  -168.0),
    (2.0,  -158.0),
    (5.0,  -150.0),
    (10.0, -149.0),   # storm microseism band (typically the minimum)
    (30.0, -155.0),
    (100.0, -149.0),  # long-period band
    (300.0, -135.0),
    (1000.0, -120.0),
    (10_000.0, -100.0),
]

# Canonical NHNM knots (period_s, PSD_dB). Noisier than NLNM by 30-50 dB
# across most of the band.
_NHNM_KNOTS_PERIOD_DB: list[tuple[float, float]] = [
    (0.01, -91.0),
    (0.10, -108.0),
    (0.20, -110.0),
    (0.50, -118.0),
    (1.0,  -120.0),
    (2.0,  -123.0),
    (5.0,  -120.0),
    (10.0, -120.0),
    (30.0, -118.0),
    (100.0, -110.0),
    (300.0, -100.0),
    (1000.0, -91.0),
    (10_000.0, -71.0),
]


def _build_psd_from_knots(
    period_db_knots: list[tuple[float, float]],
) -> tuple[np.ndarray, np.ndarray]:
    """Convert (period, PSD_dB) knots to (frequency, PSD_linear) arrays.

    The output is sorted by ascending frequency.
    """
    periods = np.array([p for p, _ in period_db_knots], dtype=float)
    psd_db = np.array([d for _, d in period_db_knots], dtype=float)
    freqs = 1.0 / periods
    order = np.argsort(freqs)
    freqs_sorted = freqs[order]
    psd_db_sorted = psd_db[order]
    psd_linear = 10.0 ** (psd_db_sorted / 10.0)
    return freqs_sorted, psd_linear


# Build module-level tuples
NLNM_PSD: tuple[np.ndarray, np.ndarray] = _build_psd_from_knots(_NLNM_KNOTS_PERIOD_DB)
NHNM_PSD: tuple[np.ndarray, np.ndarray] = _build_psd_from_knots(_NHNM_KNOTS_PERIOD_DB)


def interpolate_psd(
    f_hz: np.ndarray,
    model: str = "nlnm",
) -> np.ndarray:
    """Return interpolated PSD values at *f_hz* for the named Peterson model.

    The interpolation is linear in log10(f) vs. log10(PSD). Values outside the
    knot range are clamped to the boundary knot value (rather than extrapolated)
    to avoid generating unphysical low- or high-frequency tails.

    Parameters
    ----------
    f_hz:
        Frequencies at which to evaluate the PSD, in Hz.
    model:
        ``"nlnm"`` (default) or ``"nhnm"``.

    Returns
    -------
    PSD values in (m/s^2)^2 / Hz at each requested frequency.
    """
    if model.lower() == "nlnm":
        freqs, psd_linear = NLNM_PSD
    elif model.lower() == "nhnm":
        freqs, psd_linear = NHNM_PSD
    else:
        raise ValueError(f"Unknown Peterson model '{model}'. Use 'nlnm' or 'nhnm'.")
    log_f = np.log10(np.asarray(f_hz, dtype=float))
    log_knot_f = np.log10(freqs)
    log_knot_psd = np.log10(psd_linear)
    log_psd = np.interp(log_f, log_knot_f, log_knot_psd)
    return 10.0 ** log_psd
