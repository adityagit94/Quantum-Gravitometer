from __future__ import annotations

from pathlib import Path

import numpy as np


def _ensure_array(x: np.ndarray | float) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    return arr


def _infer_sample_rate(t: np.ndarray) -> float:
    if len(t) < 2:
        raise ValueError("Need at least two time samples to infer sample_rate_hz.")
    diffs = np.diff(t)
    if not np.all(np.isfinite(diffs)):
        raise ValueError("Time axis contains non-finite spacing.")
    diffs = diffs[diffs > 0]
    if len(diffs) == 0:
        raise ValueError("Cannot infer sampling rate")
    dt = float(np.median(diffs))
    if dt <= 0:
        raise ValueError("Unable to infer a positive median time spacing.")
    return 1.0 / dt


def load_real_ifo_csv(
    *,
    csv_path: str | Path,
    sample_rate_hz: float | None = None,
    delimiter: str = ",",
    has_header: bool = True,
) -> dict[str, np.ndarray]:
    """Load real interferometer-style data from a CSV file.

    Supported columns:
      - required: either `t` or `sample_rate_hz`
      - required: `I_meas`, `Q_meas`
      - optional: `x_true`

    The loader is defensive against malformed CSV content:
      - single-row files are normalized into 1D arrays
      - invalid rows are ignored when possible
      - non-finite rows are dropped
      - time-axis sample rate inference uses the median spacing
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    if has_header:
        data = np.genfromtxt(
            path,
            delimiter=delimiter,
            names=True,
            dtype=np.float64,
            invalid_raise=False,
            ndmin=1,
        )
        names = list(data.dtype.names or [])
        required = {"I_meas", "Q_meas"}
        missing = required.difference(names)
        if missing:
            raise ValueError(f"Missing required columns: {sorted(missing)}")
        I = _ensure_array(data["I_meas"])
        Q = _ensure_array(data["Q_meas"])
        if "t" in names:
            t = _ensure_array(data["t"])
        else:
            if sample_rate_hz is None:
                raise ValueError("Provide `sample_rate_hz` when CSV has no `t` column.")
            t = np.arange(len(I), dtype=np.float64) / float(sample_rate_hz)
        x_true = _ensure_array(data["x_true"]) if "x_true" in names else None
    else:
        raw = np.genfromtxt(path, delimiter=delimiter, dtype=np.float64, invalid_raise=False)
        raw = np.asarray(raw, dtype=np.float64)
        if raw.ndim == 0:
            raw = raw.reshape(1, 1)
        elif raw.ndim == 1:
            raw = raw.reshape(1, -1)
        if raw.shape[1] < 2:
            raise ValueError("CSV without header must have at least 2 columns: I_meas,Q_meas or t,I_meas,Q_meas")
        if raw.shape[1] == 2:
            if sample_rate_hz is None:
                raise ValueError("Provide `sample_rate_hz` when CSV has no time column.")
            I, Q = raw[:, 0], raw[:, 1]
            t = np.arange(len(I), dtype=np.float64) / float(sample_rate_hz)
            x_true = None
        elif raw.shape[1] == 3:
            t, I, Q = raw[:, 0], raw[:, 1], raw[:, 2]
            x_true = None
        else:
            t, I, Q, x_true = raw[:, 0], raw[:, 1], raw[:, 2], raw[:, 3]
        t = _ensure_array(t)
        I = _ensure_array(I)
        Q = _ensure_array(Q)
        x_true = None if x_true is None else _ensure_array(x_true)

    n_raw = len(t)
    mask = np.isfinite(t) & np.isfinite(I) & np.isfinite(Q)
    if x_true is not None:
        mask &= np.isfinite(x_true)
    t, I, Q = t[mask], I[mask], Q[mask]
    if x_true is not None:
        x_true = x_true[mask]
    dropped_count = n_raw - int(np.sum(mask))

    if np.asarray(t).size == 0:
        raise ValueError("No valid finite rows remain after CSV parsing.")
    if len(I) != len(Q) or len(I) != len(t):
        raise ValueError("Parsed CSV columns have inconsistent lengths.")
    if np.any(np.diff(t) < 0):
        raise ValueError("Time axis must be monotonic increasing; found reverse timestamps.")

    inferred_fs = None
    if sample_rate_hz is None and len(t) >= 2:
        inferred_fs = _infer_sample_rate(t)
    elif sample_rate_hz is not None:
        inferred_fs = float(sample_rate_hz)

    out = {"t": t, "I_meas": I, "Q_meas": Q, "dropped_rows": dropped_count}
    if x_true is not None:
        out["x_true"] = x_true
    if inferred_fs is not None:
        out["sample_rate_hz"] = np.asarray([inferred_fs], dtype=np.float64)
    return out
