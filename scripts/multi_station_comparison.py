#!/usr/bin/env python
"""Compare multiple gravity stations with overlaid Allan deviation, PSD, and bar chart.

Usage:
    python scripts/multi_station_comparison.py --source data/raw/sg_sample
    python scripts/multi_station_comparison.py --source archive.zip --output comparison.png
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from qgrav.datasets.gravimetry import list_stations_in_source, load_real_gravity_dataset
from qgrav.metrics import allan_deviation_overlapping, compute_psd


def main() -> None:
    parser = argparse.ArgumentParser(description="Multi-station comparison plots.")
    parser.add_argument("--source", required=True, type=Path, help="Path to data source")
    parser.add_argument("--output", type=Path, default=Path("multi_station_comparison.png"), help="Output image path")
    args = parser.parse_args()

    if not args.source.exists():
        print(f"Error: source path does not exist: {args.source}", file=sys.stderr)
        sys.exit(1)

    stations = list_stations_in_source(args.source)
    if not stations:
        print(f"No stations found in {args.source}", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(stations)} station(s). Loading data...")

    station_data: list[dict] = []
    for st in stations:
        code = st["station_code"]
        try:
            data = load_real_gravity_dataset(source_path=args.source, station_code=code)
            station_data.append({"code": code, "data": data})
        except Exception as exc:
            print(f"  Skipping {code}: {exc}")

    if not station_data:
        print("No stations could be loaded.", file=sys.stderr)
        sys.exit(1)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    # --- Allan deviation overlay ---
    ax_adev = axes[0]
    station_adev_mins: list[tuple[str, float]] = []
    for sd in station_data:
        values = sd["data"].get("gravity_residual_full", np.array([]))
        sr = sd["data"].get("sample_rate_hz", 1.0)
        if len(values) < 10:
            continue
        taus = np.logspace(0, 2, 20)
        try:
            result = allan_deviation_overlapping(values, sr, taus, backend="auto", data_type="freq")
            ax_adev.loglog(result["taus_s"], result["adev"], label=sd["code"], marker="o", markersize=3)
            if len(result["adev"]) > 0:
                station_adev_mins.append((sd["code"], float(np.min(result["adev"]))))
        except Exception:
            logger.warning("Allan deviation failed for %s", sd["code"], exc_info=True)
    ax_adev.set_xlabel("Tau (s)")
    ax_adev.set_ylabel("Allan Deviation")
    ax_adev.set_title("Overlapping Allan Deviation")
    ax_adev.legend(fontsize=7)
    ax_adev.grid(True, alpha=0.3)

    # --- PSD overlay ---
    ax_psd = axes[1]
    for sd in station_data:
        values = sd["data"].get("gravity_residual_full", np.array([]))
        sr = sd["data"].get("sample_rate_hz", 1.0)
        if len(values) < 10:
            continue
        try:
            psd_result = compute_psd(values, sr, method="welch")
            ax_psd.semilogy(psd_result["f_hz"], psd_result["psd"], label=sd["code"], linewidth=0.8)
        except Exception:
            logger.warning("PSD computation failed for %s", sd["code"], exc_info=True)
    ax_psd.set_xlabel("Frequency (Hz)")
    ax_psd.set_ylabel("PSD")
    ax_psd.set_title("Power Spectral Density")
    ax_psd.legend(fontsize=7)
    ax_psd.grid(True, alpha=0.3)

    # --- Bar chart of min ADEV ---
    ax_bar = axes[2]
    if station_adev_mins:
        codes = [s[0] for s in station_adev_mins]
        mins = [s[1] for s in station_adev_mins]
        ax_bar.bar(codes, mins, color="steelblue")
        ax_bar.set_ylabel("Min Allan Deviation")
        ax_bar.set_title("Best Allan Deviation per Station")
        ax_bar.tick_params(axis="x", rotation=45)
    else:
        ax_bar.text(0.5, 0.5, "No ADEV data", ha="center", va="center", transform=ax_bar.transAxes)

    fig.tight_layout()
    fig.savefig(args.output, dpi=150)
    print(f"Saved comparison plot to {args.output}")
    plt.close(fig)


if __name__ == "__main__":
    main()
