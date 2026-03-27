from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AtomSourceConfig:
    """Parameters describing the detected atomic source used by a study.

    This separates the source model from the pulse sequence and phase model.
    The object is intentionally small and JSON-friendly so that it can be
    carried into reports without extra conversion work.
    """

    n_atoms_total: int
    seed: int
    cloud_radius_m: float
    temp_xy_K: float
    temp_z_K: float
    detector_time_s: float
    detector_radius_m: float
    multiport: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def source_summary_rows(config: AtomSourceConfig, detected_count: int) -> dict[str, Any]:
    total = max(int(config.n_atoms_total), 1)
    return {
        'Total atoms': int(config.n_atoms_total),
        'Detected atoms': int(detected_count),
        'Detected fraction': float(detected_count / total),
        'Cloud radius (m)': float(config.cloud_radius_m),
        'Temp XY (K)': float(config.temp_xy_K),
        'Temp Z (K)': float(config.temp_z_K),
        'Detector time (s)': float(config.detector_time_s),
        'Detector radius (m)': float(config.detector_radius_m),
        'Multiport source': bool(config.multiport),
    }
