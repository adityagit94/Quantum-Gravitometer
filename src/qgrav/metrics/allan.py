from __future__ import annotations

from functools import lru_cache
import logging
from typing import Literal

import numpy as np

AllanBackend = Literal["auto", "custom", "allantools"]
AllanDataType = Literal["freq", "phase"]

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _import_allantools_module():
    """Import AllanTools.

    In this repository a vendored copy is installed as a top-level ``allantools`` package,
    so this works offline in editable installs while remaining compatible with an external
    AllanTools installation.
    """
    try:
        import allantools as at  # type: ignore
        return at
    except Exception:
        logger.exception("Failed to import AllanTools")
        return None


def available_allan_backends() -> list[str]:
    backends = ["custom"]
    if _import_allantools_module() is not None:
        backends.append("allantools")
    return backends


def _validate_inputs(x: np.ndarray, sample_rate_hz: float, taus_s: np.ndarray) -> tuple[np.ndarray, float, np.ndarray]:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError("Allan deviation input must be 1D.")
    n = len(x)
    if n < 10:
        raise ValueError("Need at least 10 samples.")
    if float(sample_rate_hz) <= 0:
        raise ValueError("sample_rate_hz must be positive.")

    taus_s = np.asarray(taus_s, dtype=np.float64)
    if taus_s.ndim != 1 or len(taus_s) == 0:
        raise ValueError("taus_s must be a non-empty 1D array.")
    if not np.all(np.isfinite(taus_s)) or np.any(taus_s <= 0):
        raise ValueError("taus_s must contain only positive finite values.")
    return x, float(sample_rate_hz), taus_s


def _custom_oadev_freq(x: np.ndarray, sample_rate_hz: float, taus_s: np.ndarray) -> dict[str, np.ndarray]:
    """Custom overlapping Allan deviation for directly sampled measurement values.

    This matches AllanTools ``oadev(..., data_type='freq')``. In AllanTools terminology,
    ``freq`` means the sampled series represents the measured quantity directly (for this
    project: displacement estimates), not literal oscillator frequency.
    """
    tau0 = 1.0 / sample_rate_hz
    ms = np.maximum(1, np.rint(taus_s / tau0).astype(int))
    taus_actual: list[float] = []
    adev: list[float] = []

    csum = np.concatenate([[0.0], np.cumsum(x, dtype=np.float64)])
    n = len(x)
    for m in ms:
        if 2 * m > n:
            continue
        # Overlapping block means, length n-m+1
        means = (csum[m:] - csum[:-m]) / float(m)
        diffs = means[m:] - means[:-m]
        if len(diffs) == 0:
            continue
        taus_actual.append(m * tau0)
        adev.append(float(np.sqrt(0.5 * np.mean(diffs**2))))

    return {"taus_s": np.asarray(taus_actual, dtype=np.float64), "adev": np.asarray(adev, dtype=np.float64)}


def _custom_oadev_phase(x: np.ndarray, sample_rate_hz: float, taus_s: np.ndarray) -> dict[str, np.ndarray]:
    """Custom overlapping Allan deviation for phase-like time-series data.

    This matches AllanTools ``oadev(..., data_type='phase')``.
    """
    tau0 = 1.0 / sample_rate_hz
    ms = np.maximum(1, np.rint(taus_s / tau0).astype(int))
    taus_actual: list[float] = []
    adev: list[float] = []

    n = len(x)
    for m in ms:
        if 2 * m >= n:
            continue
        d2 = x[2 * m:] - 2.0 * x[m:-m] + x[:-2 * m]
        if len(d2) == 0:
            continue
        taus_actual.append(m * tau0)
        adev.append(float(np.sqrt(np.mean(d2**2) / (2.0 * (m * tau0) ** 2))))

    return {"taus_s": np.asarray(taus_actual, dtype=np.float64), "adev": np.asarray(adev, dtype=np.float64)}


def _resolve_backend(backend: AllanBackend) -> str:
    backend = str(backend).strip().lower()  # type: ignore[assignment]
    if backend not in {"auto", "custom", "allantools"}:
        raise ValueError("backend must be one of: auto, custom, allantools.")
    if backend == "auto":
        return "allantools" if _import_allantools_module() is not None else "custom"
    if backend == "allantools" and _import_allantools_module() is None:
        raise RuntimeError(
            "AllanTools backend requested but unavailable. Install AllanTools or use the vendored copy with SciPy installed."
        )
    return backend


def allan_deviation_overlapping(
    x: np.ndarray,
    sample_rate_hz: float,
    taus_s: np.ndarray,
    *,
    backend: AllanBackend = "auto",
    data_type: AllanDataType = "freq",
) -> dict[str, np.ndarray | str]:
    """Compute overlapping Allan deviation using the requested backend.

    Parameters
    ----------
    x:
        Input 1D time series.
    sample_rate_hz:
        Sampling rate in Hz.
    taus_s:
        Array of tau values in seconds.
    backend:
        ``auto`` (prefer AllanTools if available), ``custom``, or ``allantools``.
    data_type:
        AllanTools-style data interpretation:
        - ``freq`` for directly sampled measurement values (recommended for this project)
        - ``phase`` for phase-like integrated series
    """
    x, sample_rate_hz, taus_s = _validate_inputs(x, sample_rate_hz, taus_s)
    data_type = str(data_type).strip().lower()  # type: ignore[assignment]
    if data_type not in {"freq", "phase"}:
        raise ValueError("data_type must be either 'freq' or 'phase'.")

    resolved_backend = _resolve_backend(backend)
    if resolved_backend == "allantools":
        at = _import_allantools_module()
        if at is None:  # pragma: no cover - guarded above
            raise RuntimeError("AllanTools import unexpectedly failed.")
        taus2, ad, _, _ = at.oadev(x, rate=sample_rate_hz, data_type=data_type, taus=taus_s)
        taus2 = np.asarray(taus2, dtype=np.float64)
        ad = np.asarray(ad, dtype=np.float64)
        valid = np.isfinite(taus2) & np.isfinite(ad)
        return {
            "taus_s": taus2[valid],
            "adev": ad[valid],
            "backend": resolved_backend,
            "data_type": data_type,
        }

    if data_type == "phase":
        out = _custom_oadev_phase(x, sample_rate_hz, taus_s)
    else:
        out = _custom_oadev_freq(x, sample_rate_hz, taus_s)
    return {
        **out,
        "backend": resolved_backend,
        "data_type": data_type,
    }


# Alias used by the PRD and pipeline code
compute_adev = allan_deviation_overlapping


def identify_noise_type(taus_s: np.ndarray, adev: np.ndarray) -> dict:
    """Identify dominant noise type from Allan deviation log-log slope.

    Noise classification based on power-law slope of sigma(tau) ~ tau^mu:
      mu < -0.75 : white phase noise
      -0.75 <= mu < -0.25 : flicker phase noise
      -0.25 <= mu < 0.25  : white frequency noise
      0.25 <= mu < 0.75   : flicker frequency noise
      mu >= 0.75           : random walk frequency noise

    Returns dict with slope, noise_type, fit_r2, description.
    If fewer than 3 valid points, returns noise_type='insufficient_data'.
    """
    taus_s = np.asarray(taus_s, dtype=np.float64)
    adev = np.asarray(adev, dtype=np.float64)
    valid = (taus_s > 0) & (adev > 0) & np.isfinite(taus_s) & np.isfinite(adev)
    if np.sum(valid) < 3:
        return {
            "slope": float("nan"),
            "noise_type": "insufficient_data",
            "fit_r2": float("nan"),
            "description": "Fewer than 3 valid ADEV points for slope fitting.",
        }

    log_tau = np.log10(taus_s[valid])
    log_adev = np.log10(adev[valid])
    coeffs = np.polyfit(log_tau, log_adev, 1)
    slope = float(coeffs[0])

    # Classify based on slope boundaries
    if slope < -0.75:
        noise_type = "white_phase"
        description = "White phase noise (slope < -0.75)"
    elif slope < -0.25:
        noise_type = "flicker_phase"
        description = "Flicker phase noise (-0.75 <= slope < -0.25)"
    elif slope < 0.25:
        noise_type = "white_frequency"
        description = "White frequency noise (-0.25 <= slope < 0.25)"
    elif slope < 0.75:
        noise_type = "flicker_frequency"
        description = "Flicker frequency noise (0.25 <= slope < 0.75)"
    else:
        noise_type = "random_walk_frequency"
        description = "Random walk frequency noise (slope >= 0.75)"

    # R-squared for fit quality
    fitted = np.polyval(coeffs, log_tau)
    ss_res = float(np.sum((log_adev - fitted) ** 2))
    ss_tot = float(np.sum((log_adev - np.mean(log_adev)) ** 2))
    fit_r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0

    return {
        "method": "log_log_slope_fit",
        "slope": slope,
        "noise_type": noise_type,
        "fit_r2": fit_r2,
        "description": description,
    }


_ACF_ALPHA_INT_TO_NAME = {
    2: "white_phase",
    1: "flicker_phase",
    0: "white_frequency",
    -1: "flicker_frequency",
    -2: "random_walk_frequency",
    -3: "flicker_walk_frequency",
    -4: "random_run_frequency",
}


def identify_noise_type_acf(
    x: np.ndarray,
    *,
    data_type: str = "freq",
    averaging_factor: int = 1,
    dmin: int = 0,
    dmax: int = 2,
) -> dict:
    """Identify noise type using lag-1 autocorrelation (Riley 2004).

    Wraps :func:`allantools.ci.autocorr_noise_id`. The ACF method works on
    the *time series* (not on the Allan deviation curve) and is more robust
    than slope-fitting on the ADEV log-log plot, especially for mixed
    noise.

    Parameters
    ----------
    x:
        Phase or fractional-frequency time series. Minimum length ~30.
    data_type:
        ``"phase"`` or ``"freq"``.
    averaging_factor:
        Decimation factor before differencing.
    dmin, dmax:
        Bounds on the number of differentiations the algorithm performs.

    Returns
    -------
    dict with keys ``method``, ``noise_type``, ``alpha_int``, ``alpha``,
    ``d``, ``rho``. If the series is too short to identify, returns a
    safe sentinel.

    References
    ----------
    Riley, W.J., *Handbook of Frequency Stability Analysis*, NIST SP1065 (2008).
    """
    arr = np.asarray(x, dtype=np.float64)
    # The vendored allantools requires len >= 30 after decimation.
    if arr.size < max(30, 2 * averaging_factor):
        return {
            "method": "lag1_autocorrelation",
            "noise_type": "insufficient_data",
            "alpha_int": None,
            "alpha": float("nan"),
            "d": 0,
            "rho": float("nan"),
            "description": "Time series too short for ACF noise-type ID.",
        }
    try:
        from allantools.ci import autocorr_noise_id  # type: ignore

        alpha_int, alpha, d, rho = autocorr_noise_id(
            arr, af=int(averaging_factor), data_type=data_type,
            dmin=int(dmin), dmax=int(dmax),
        )
        noise_type = _ACF_ALPHA_INT_TO_NAME.get(int(alpha_int), f"alpha_int={alpha_int}")
        return {
            "method": "lag1_autocorrelation",
            "noise_type": noise_type,
            "alpha_int": int(alpha_int),
            "alpha": float(alpha),
            "d": int(d),
            "rho": float(rho),
            "description": (
                f"ACF-based ID (Riley 2004): alpha={alpha:+.2f}, "
                f"differentiations d={d}, lag-1 ACF rho={rho:+.3f}."
            ),
        }
    except (NotImplementedError, ValueError, ZeroDivisionError) as exc:
        return {
            "method": "lag1_autocorrelation",
            "noise_type": "indeterminate",
            "alpha_int": None,
            "alpha": float("nan"),
            "d": 0,
            "rho": float("nan"),
            "description": f"ACF noise-type ID failed: {exc!r}",
        }


def allan_minimum(taus_s: np.ndarray, adev: np.ndarray) -> dict:
    """Find the minimum of the Allan deviation curve.

    Returns dict with min_adev, min_tau_s, min_index.
    """
    taus_s = np.asarray(taus_s, dtype=np.float64)
    adev = np.asarray(adev, dtype=np.float64)
    valid = np.isfinite(adev) & (adev > 0)
    if not np.any(valid):
        return {"min_adev": float("nan"), "min_tau_s": float("nan"), "min_index": -1}
    valid_idx = np.where(valid)[0]
    best = valid_idx[np.argmin(adev[valid])]
    return {
        "min_adev": float(adev[best]),
        "min_tau_s": float(taus_s[best]),
        "min_index": int(best),
    }
