from __future__ import annotations

import numpy as np


def _validate_inputs(x: np.ndarray, sample_rate_hz: float) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 1:
        raise ValueError("PSD input must be a 1D array.")
    if len(x) < 4:
        raise ValueError("Need at least 4 samples.")
    if float(sample_rate_hz) <= 0:
        raise ValueError("sample_rate_hz must be positive.")
    return x


def _periodogram(x: np.ndarray, sample_rate_hz: float) -> dict[str, np.ndarray]:
    n = len(x)
    x = x - np.mean(x)
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(n, d=1.0 / float(sample_rate_hz))
    psd = (np.abs(X) ** 2) / (float(sample_rate_hz) * n)
    if n % 2 == 0:
        psd[1:-1] *= 2.0
    else:
        psd[1:] *= 2.0
    return {"f_hz": f, "psd": psd}


def _welch(x: np.ndarray, sample_rate_hz: float, nperseg: int, noverlap: int) -> dict[str, np.ndarray]:
    if nperseg < 4:
        raise ValueError("nperseg must be >= 4 for Welch PSD.")
    if noverlap < 0 or noverlap >= nperseg:
        raise ValueError("noverlap must satisfy 0 <= noverlap < nperseg.")
    if len(x) < nperseg:
        raise ValueError("Signal shorter than Welch segment length.")

    step = nperseg - noverlap
    window = np.hanning(nperseg)
    window_power = np.sum(window**2)
    starts = range(0, len(x) - nperseg + 1, step)

    psd_accum = None
    count = 0
    for start in starts:
        seg = x[start:start + nperseg]
        seg = seg - np.mean(seg)
        segw = seg * window
        X = np.fft.rfft(segw)
        psd = (np.abs(X) ** 2) / (float(sample_rate_hz) * window_power)
        if nperseg % 2 == 0:
            psd[1:-1] *= 2.0
        else:
            psd[1:] *= 2.0
        if psd_accum is None:
            psd_accum = psd
        else:
            psd_accum += psd
        count += 1

    if count == 0 or psd_accum is None:
        raise ValueError("No Welch segments were generated.")

    f = np.fft.rfftfreq(nperseg, d=1.0 / float(sample_rate_hz))
    return {"f_hz": f, "psd": psd_accum / count}


def compute_psd(
    x: np.ndarray,
    sample_rate_hz: float,
    *,
    method: str = "periodogram",
    nperseg: int | None = None,
    noverlap: int | None = None,
) -> dict[str, np.ndarray]:
    """Compute a one-sided PSD.

    Supported methods:
      - ``periodogram``: simple FFT-based estimate.
      - ``welch``: averaged, windowed estimate for smoother and more reproducible spectra.
    """
    x = _validate_inputs(x, sample_rate_hz)
    method = method.lower().strip()
    if method == "periodogram":
        return _periodogram(x, sample_rate_hz)
    if method == "welch":
        nperseg = int(nperseg or min(1024, len(x)))
        nperseg = min(nperseg, len(x))
        noverlap = int(noverlap if noverlap is not None else nperseg // 2)
        return _welch(x, sample_rate_hz, nperseg, noverlap)
    raise ValueError(f"Unsupported PSD method: {method}")
