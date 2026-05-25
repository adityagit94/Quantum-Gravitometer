"""Shared helpers for the pipeline package."""
from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pathlib import Path as _PathForMPL
_MPLDIR = _PathForMPL.home() / ".qgrav_mpl"
_MPLDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPLDIR))

import matplotlib
if str(matplotlib.get_backend()).lower() != "tkagg":
    matplotlib.use("Agg")
import numpy as np

from qgrav import __version__
from qgrav.metrics import allan_deviation_overlapping

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    plots_dir: Path
    data_path: Path
    config_copy: Path
    metrics_path: Path
    summary_path: Path
    run_metadata_path: Path


# ---------- common helpers ----------
def _make_run_dir(base: Path, name: str) -> RunPaths:
    base.mkdir(parents=True, exist_ok=True)
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in name.strip()) or "run"
    for _ in range(10):
        run_id = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{uuid.uuid4().hex[:8]}_{safe}"
        run_dir = base / run_id
        plots_dir = run_dir / "plots"
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
            plots_dir.mkdir(parents=True, exist_ok=False)
            return RunPaths(
                run_dir=run_dir,
                plots_dir=plots_dir,
                data_path=run_dir / "data.npz",
                config_copy=run_dir / "config_used.yaml",
                metrics_path=run_dir / "metrics.json",
                summary_path=run_dir / "SUMMARY.md",
                run_metadata_path=run_dir / "run_metadata.json",
            )
        except FileExistsError:
            time.sleep(0.001)
    raise RuntimeError("Unable to create unique run directory")


def _logspace_taus(duration_s: float, sample_rate_hz: float, n: int = 25) -> np.ndarray:
    tau0 = 1.0 / float(sample_rate_hz)
    tau_max = max(2.0 * tau0, 0.25 * float(duration_s))
    return np.logspace(np.log10(tau0), np.log10(tau_max), n)


def _jsonable(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    # Check datetime64/timedelta64 BEFORE generic np.integer/np.floating,
    # because np.timedelta64 inherits from np.signedinteger in NumPy 2.x.
    if isinstance(obj, np.datetime64):
        return str(obj)
    if isinstance(obj, np.timedelta64):
        # Preserve sub-second precision as float seconds
        return float(obj / np.timedelta64(1, "s")) if not np.isnat(obj) else None
    if isinstance(obj, (np.floating, np.integer, np.bool_)):
        return obj.item()
    if isinstance(obj, (np.str_, np.bytes_)):
        return str(obj)
    return obj


def _match_taus(taus1: np.ndarray, taus2: np.ndarray, rtol: float = 1e-9):
    """Match tau values between two arrays using relative tolerance."""
    taus1 = np.asarray(taus1, dtype=np.float64)
    taus2 = np.asarray(taus2, dtype=np.float64)
    if len(taus1) == 0 or len(taus2) == 0:
        return np.array([], dtype=int), np.array([], dtype=int)

    order2 = np.argsort(taus2)
    sorted2 = taus2[order2]
    used = np.zeros(len(taus2), dtype=bool)
    idx1, idx2 = [], []

    for i, t1 in enumerate(taus1):
        pos = np.searchsorted(sorted2, t1)
        best_j = -1
        best_diff = np.inf
        for candidate in (pos - 1, pos):
            if 0 <= candidate < len(sorted2):
                orig_j = int(order2[candidate])
                if used[orig_j]:
                    continue
                diff = abs(t1 - sorted2[candidate])
                thr = rtol * max(abs(t1), abs(sorted2[candidate]), 1e-30)
                if diff <= thr and diff < best_diff:
                    best_diff = diff
                    best_j = orig_j
        if best_j >= 0:
            used[best_j] = True
            idx1.append(i)
            idx2.append(best_j)

    return np.array(idx1, dtype=int), np.array(idx2, dtype=int)


def _compare_allan_backends(
    x: np.ndarray,
    fs: float,
    taus: np.ndarray,
    *,
    primary_backend: str,
    reference_backend: str,
    data_type: str,
) -> dict[str, Any]:
    primary = allan_deviation_overlapping(x, fs, taus, backend=primary_backend, data_type=data_type)
    reference = allan_deviation_overlapping(x, fs, taus, backend=reference_backend, data_type=data_type)
    taus1 = np.asarray(primary["taus_s"], dtype=np.float64)
    adev1 = np.asarray(primary["adev"], dtype=np.float64)
    taus2 = np.asarray(reference["taus_s"], dtype=np.float64)
    adev2 = np.asarray(reference["adev"], dtype=np.float64)

    i1, i2 = _match_taus(taus1, taus2)
    if len(i1) == 0:
        return {
            "primary_backend": primary_backend,
            "reference_backend": reference_backend,
            "data_type": data_type,
            "tau_count": 0,
            "note": "No common tau values available for backend comparison.",
        }
    v1 = adev1[i1]
    v2 = adev2[i2]
    abs_diff = np.abs(v1 - v2)
    rel_diff = abs_diff / np.maximum(np.abs(v2), 1e-30)
    return {
        "primary_backend": primary_backend,
        "reference_backend": reference_backend,
        "data_type": data_type,
        "tau_count": int(len(i1)),
        "max_abs_diff": float(np.max(abs_diff)),
        "mean_abs_diff": float(np.mean(abs_diff)),
        "max_rel_diff": float(np.max(rel_diff)),
        "mean_rel_diff": float(np.mean(rel_diff)),
    }


def _stats_cfg(cfg: dict[str, Any]) -> tuple[str, int, int, str, str, bool, str]:
    stats_cfg = cfg.get("stats", {}) if isinstance(cfg.get("stats", {}), dict) else {}
    psd_method = str(stats_cfg.get("psd_method", "welch")).strip().lower()
    nperseg = int(stats_cfg.get("welch_nperseg", 1024))
    noverlap = int(stats_cfg.get("welch_noverlap", max(1, nperseg // 2)))
    metrics_backend = str(stats_cfg.get("metrics_backend", stats_cfg.get("allan_backend", "auto"))).strip().lower()
    allan_data_type = str(stats_cfg.get("allan_data_type", "freq")).strip().lower()
    compare_allan_backends = bool(stats_cfg.get("compare_allan_backends", False))
    comparison_backend = str(stats_cfg.get("comparison_backend", "custom")).strip().lower()
    return psd_method, nperseg, noverlap, metrics_backend, allan_data_type, compare_allan_backends, comparison_backend


def _write_run_metadata(path: Path, config: dict[str, Any], metrics: dict[str, Any]) -> None:
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "config": _jsonable(config),
        "version": __version__,
        "metrics_keys": sorted(metrics.keys()),
    }
    path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def _write_summary(path: Path, metrics: dict[str, Any]) -> None:
    lines = ["# Run Summary", ""]
    lines.append(f"- Bench type: `{metrics.get('bench_type')}`")
    lines.append(f"- Sample rate: `{metrics.get('sample_rate_hz')}` Hz")
    lines.append(f"- PSD method: `{metrics.get('psd_method')}`")
    lines.append(f"- Allan backend used: `{metrics.get('allan_backend_used')}`")
    lines.append(f"- Allan data type: `{metrics.get('allan_data_type')}`")
    if metrics.get("bench_type") == "real_gravity":
        lines.extend([
            "",
            "## Real gravimetry dataset",
            f"- Station code: `{metrics.get('station_code')}`",
            f"- Longitude (deg): `{metrics.get('longitude_deg')}`",
            f"- Latitude (deg): `{metrics.get('latitude_deg')}`",
            f"- Record start: `{metrics.get('record_start')}`",
            f"- Record end: `{metrics.get('record_end')}`",
            f"- Mean: `{metrics.get('gravity_summary', {}).get('mean')}`",
            f"- Std: `{metrics.get('gravity_summary', {}).get('std')}`",
            f"- Gap count: `{metrics.get('gap_report', {}).get('gap_count')}`",
            f"- Missing samples estimate: `{metrics.get('gap_report', {}).get('missing_samples_estimate')}`",
            f"- Analysis segment samples: `{metrics.get('analysis_segment', {}).get('segment_samples')}`",
            f"- Dropped malformed rows: `{metrics.get('dropped_rows', 0)}`",
        ])
        for warning in metrics.get("unit_warnings", []):
            lines.append(f"- Unit warning: `{warning}`")
    elif metrics.get("have_truth"):
        base = metrics["baseline"]
        imp = metrics["improved"]
        lines.extend([
            "",
            "## Error statistics",
            f"- Baseline RMSE: `{base['rmse']}`",
            f"- Improved RMSE: `{imp['rmse']}`",
            f"- RMSE improvement: `{metrics.get('rmse_improvement_percent')}` %",
            f"- Baseline MAE: `{base['mae']}`",
            f"- Improved MAE: `{imp['mae']}`",
            f"- Baseline time correlation: `{base['time_corr']}`",
            f"- Improved time correlation: `{imp['time_corr']}`",
        ])
    if "noise_identification" in metrics:
        ni = metrics["noise_identification"]
        lines.append(f"- Dominant noise type: `{ni.get('noise_type', 'unknown')}`")
        slope_val = ni.get("slope")
        if slope_val is not None and np.isfinite(slope_val):
            lines.append(f"- ADEV slope: `{slope_val:.3f}`")
    if "noise_identification_baseline" in metrics:
        ni_b = metrics["noise_identification_baseline"]
        ni_i = metrics["noise_identification_improved"]
        _slope_b = ni_b.get("slope", float("nan"))
        _slope_i = ni_i.get("slope", float("nan"))
        lines.append(f"- Baseline noise type: `{ni_b.get('noise_type', 'unknown')}` (slope={float(_slope_b):.3f})")
        lines.append(f"- Improved noise type: `{ni_i.get('noise_type', 'unknown')}` (slope={float(_slope_i):.3f})")
    if "allan_minimum" in metrics:
        am = metrics["allan_minimum"]
        lines.append(f"- Allan minimum: `{am.get('min_adev', 'N/A')}` at tau=`{am.get('min_tau_s', 'N/A')}` s")
    if "allan_improvement_percent_mean" in metrics:
        lines.append(f"- Mean Allan improvement: `{metrics['allan_improvement_percent_mean']}` %")
    if "simulation" in metrics:
        sim = metrics["simulation"]
        lines.extend(["", "## AISim simulation"])
        summary_rows = sim.get("summary_rows", {}) if isinstance(sim, dict) else {}
        if isinstance(summary_rows, dict) and summary_rows:
            for key, value in summary_rows.items():
                lines.append(f"- {key}: `{value}`")
        else:
            lines.extend([f"- Backend: `{sim.get('backend')}`", f"- Model: `{sim.get('model')}`"])
        truth = sim.get("truth_checks", {}) if isinstance(sim, dict) else {}
        if isinstance(truth, dict) and truth:
            lines.extend([
                f"- Truth checks passed: `{truth.get('passed_count')}/{truth.get('total_count')}`",
                f"- All truth checks passed: `{truth.get('all_passed')}`",
            ])
    if "allan_backend_comparison" in metrics:
        comp = metrics["allan_backend_comparison"]
        lines.extend([
            "",
            "## Allan backend comparison",
            f"- Primary backend: `{comp['primary_backend']}`",
            f"- Reference backend: `{comp['reference_backend']}`",
            f"- Tau count: `{comp['tau_count']}`",
            f"- Mean relative difference: `{comp.get('mean_rel_diff')}`",
            f"- Max relative difference: `{comp.get('max_rel_diff')}`",
        ])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
