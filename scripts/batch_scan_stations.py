#!/usr/bin/env python
"""Scan all stations in a gravity data source and record quality metrics to CSV.

Usage:
    python scripts/batch_scan_stations.py --source data/raw/sg_sample
    python scripts/batch_scan_stations.py --source archive.zip --output results.csv
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path

import numpy as np

# Ensure the project root is importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qgrav.datasets.gravimetry import list_stations_in_source, load_real_gravity_dataset
from qgrav.metrics import allan_deviation_overlapping, compute_psd

logger = logging.getLogger(__name__)


def scan_station(source_path: Path, station_code: str) -> dict[str, object]:
    """Load one station and compute summary quality metrics."""
    row: dict[str, object] = {"station_code": station_code}
    try:
        data = load_real_gravity_dataset(source_path=source_path, station_code=station_code)
    except Exception as exc:
        row["error"] = str(exc)
        return row

    values = data.get("gravity_residual_full", np.array([]))
    row["n_samples"] = len(values)
    row["dropped_rows"] = data.get("dropped_rows", 0)

    if len(values) < 10:
        row["error"] = "Too few samples for metrics"
        return row

    row["mean"] = float(np.nanmean(values))
    row["std"] = float(np.nanstd(values))
    row["min"] = float(np.nanmin(values))
    row["max"] = float(np.nanmax(values))

    sample_rate = data.get("sample_rate_hz", 1.0)
    try:
        taus = np.logspace(0, 2, 10)
        adev_result = allan_deviation_overlapping(
            values, sample_rate, taus, backend="auto", data_type="freq"
        )
        if len(adev_result["adev"]) > 0:
            row["adev_min"] = float(np.min(adev_result["adev"]))
    except Exception:
        logger.warning("Allan deviation failed for %s", station_code, exc_info=True)

    try:
        psd_result = compute_psd(values, sample_rate, method="welch")
        if len(psd_result["psd"]) > 0:
            row["psd_median"] = float(np.median(psd_result["psd"]))
    except Exception:
        logger.warning("PSD computation failed for %s", station_code, exc_info=True)

    return row


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch scan gravity stations for quality metrics.")
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Path to data source (directory, .zip, .ggp, .csv)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("batch_station_metrics.csv"), help="Output CSV path"
    )
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Error: source path does not exist: {args.source}", file=sys.stderr)
        sys.exit(1)

    stations = list_stations_in_source(args.source)
    if not stations:
        print(f"No stations found in {args.source}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(stations)} station(s). Scanning...")

    rows: list[dict[str, object]] = []
    for st in stations:
        code = st["station_code"]
        print(f"  Scanning {code} ...")
        row = scan_station(args.source, code)
        rows.append(row)

    # Collect all field names from rows
    fieldnames: list[str] = []
    for r in rows:
        for k in r:
            if k not in fieldnames:
                fieldnames.append(k)

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} station(s) to {args.output}")


if __name__ == "__main__":
    main()
