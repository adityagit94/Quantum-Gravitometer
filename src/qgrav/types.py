"""Type definitions for key qgrav data structures.

These TypedDicts document the shape of dictionaries returned by public APIs
so that calling code can benefit from static type-checking and IDE
autocompletion.
"""

from __future__ import annotations

from typing import Any, NotRequired

import numpy as np
from typing_extensions import TypedDict


class GravityDataset(TypedDict):
    """Return type of ``load_real_gravity_dataset``."""

    gravity_residual_full: np.ndarray
    gravity_residual: np.ndarray
    t_full: np.ndarray
    t: np.ndarray
    timestamps_full: np.ndarray
    timestamps: np.ndarray
    sample_rate_hz: float
    station_code: str
    source_path: str
    source_kind: str
    record_start: str
    record_end: str
    gap_report: dict[str, Any]
    analysis_segment: dict[str, Any]
    units: NotRequired[str]
    unit_warnings: NotRequired[list[str]]
    dropped_rows: NotRequired[int]
    latitude_deg: NotRequired[float]
    longitude_deg: NotRequired[float]


class AllanResult(TypedDict):
    """Return type of ``allan_deviation_overlapping``."""

    taus_s: np.ndarray
    adev: np.ndarray
    backend: str
    data_type: str


class PSDResult(TypedDict):
    """Return type of ``compute_psd``."""

    f_hz: np.ndarray
    psd: np.ndarray
    method: str
    nperseg: int
    noverlap: int


class AiSimResult(TypedDict, total=False):
    """Return type of ``run_aisim_*`` functions."""

    taus_s: np.ndarray
    excited_fraction: np.ndarray
    phases_rad: np.ndarray
    gravity_values_m_s2: np.ndarray
    amplitudes_m: np.ndarray
    n_atoms: int
    model: str
    backend: str
    study_scope: str
    shot_noise_sensitivity_m_s2_per_sqrt_hz: float
    summary_rows: dict[str, Any]
    truth_checks: dict[str, Any]
    plot_specs: list[dict[str, Any]]
