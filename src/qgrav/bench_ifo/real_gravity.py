from __future__ import annotations

from pathlib import Path
from typing import Any

from qgrav.datasets import load_real_gravity_dataset


def load_real_gravity(
    *,
    source_path: str | Path,
    station_code: str | None = None,
    metadata_path: str | Path | None = None,
    segment_strategy: str = "longest_contiguous",
    gap_tolerance_fraction: float = 0.1,
) -> dict[str, Any]:
    return load_real_gravity_dataset(
        source_path=source_path,
        station_code=station_code,
        metadata_path=metadata_path,
        segment_strategy=segment_strategy,
        gap_tolerance_fraction=gap_tolerance_fraction,
    )
