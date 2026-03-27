from __future__ import annotations

import numpy as np


def add_white_noise(x: np.ndarray, std: float, *, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if std <= 0:
        return arr.copy()
    return arr + rng.normal(0.0, float(std), size=arr.shape)


def add_bias(x: np.ndarray, bias: float) -> np.ndarray:
    return np.asarray(x, dtype=np.float64) + float(bias)


def add_random_walk_drift(x: np.ndarray, step_std: float, *, rng: np.random.Generator) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64)
    if step_std <= 0:
        return arr.copy()
    return arr + np.cumsum(rng.normal(0.0, float(step_std), size=arr.shape))


def add_outlier_spikes(
    x: np.ndarray,
    *,
    rate: float,
    spike_std: float,
    rng: np.random.Generator,
) -> np.ndarray:
    arr = np.asarray(x, dtype=np.float64).copy()
    if rate <= 0 or spike_std <= 0:
        return arr
    mask = rng.uniform(0.0, 1.0, size=arr.shape) < float(rate)
    if np.any(mask):
        arr[mask] += rng.normal(0.0, float(spike_std), size=int(np.sum(mask)))
    return arr
