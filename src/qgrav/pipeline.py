from __future__ import annotations

import json
import logging
import os
import time
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
import matplotlib.pyplot as plt
import numpy as np

from qgrav import __version__
from qgrav.algorithms import estimate_displacement_baseline, estimate_displacement_improved
from qgrav.bench_ifo import generate_virtual_ifo, load_real_gravity, load_real_ifo_csv
from qgrav.config import load_config, resolve_project_relative_path, resolve_runs_dir, validate_config
from qgrav.metrics import allan_deviation_overlapping, compute_error_statistics, compute_psd, improvement_percent
from qgrav.reporting import build_html_report
from qgrav.sim_ai import run_simulation_from_config
from qgrav.validation import curve_correlation

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
        run_id = f"{datetime.now():%Y%m%d_%H%M%S_%f}_{safe}"
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
    if isinstance(obj, (np.floating, np.integer, np.bool_)):
        return obj.item()
    return obj


def _match_taus(taus1: np.ndarray, taus2: np.ndarray, rtol: float = 1e-9):
    """Match tau values between two arrays using relative tolerance.

    Returns (indices_in_taus1, indices_in_taus2) for matched pairs.
    Each element in taus2 is matched at most once (first-come-first-served).
    Uses sorted search for O(n log n) performance.
    """
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


def _add_simulation(metrics: dict[str, Any], save_dict: dict[str, np.ndarray], sim_cfg: dict[str, Any]) -> None:
    simulation_result = run_simulation_from_config(sim_cfg)
    if simulation_result is None:
        return
    metrics["simulation"] = {k: _jsonable(v) for k, v in simulation_result.items() if not isinstance(v, np.ndarray)}
    for key, value in simulation_result.items():
        if isinstance(value, np.ndarray):
            save_dict[f"sim_{key}"] = np.asarray(value, dtype=np.float64)


def _plot_series_from_spec(spec: dict[str, Any], data: Any, out_path: Path) -> Path:
    try:
        x = np.asarray(data[f"sim_{spec['x_key']}"], dtype=np.float64)
        x_scale = float(spec.get("x_scale", 1.0))
        plt.figure(figsize=(9.0, 5.0))
        for series in spec.get("series", []):
            y = np.asarray(data[f"sim_{series['key']}"], dtype=np.float64)
            label = str(series.get("label", series["key"]))
            kind = str(series.get("kind", "line"))
            if kind == "line_markers":
                plt.plot(x * x_scale, y, marker="o", markersize=2.5, linewidth=1.2, label=label)
            elif kind == "dashed":
                plt.plot(x * x_scale, y, linestyle="--", linewidth=1.3, label=label)
            else:
                plt.plot(x * x_scale, y, linewidth=1.3, label=label)
        plt.xlabel(str(spec.get("x_label", spec["x_key"])))
        plt.ylabel(str(spec.get("y_label", "value")))
        plt.title(str(spec.get("title", "Simulation plot")))
        if len(spec.get("series", [])) > 1:
            plt.legend()
        plt.tight_layout()
        plt.savefig(out_path, dpi=160)
        return out_path
    finally:
        plt.close("all")


def _make_simulation_plots(paths: RunPaths, metrics: dict[str, Any]) -> list[dict[str, str]]:
    sim = metrics.get("simulation")
    if not isinstance(sim, dict):
        return []
    plot_specs = sim.get("plot_specs", [])
    if not isinstance(plot_specs, list):
        return []
    data = np.load(paths.data_path, allow_pickle=False)
    rendered: list[dict[str, str]] = []
    for idx, spec in enumerate(plot_specs):
        if not isinstance(spec, dict):
            continue
        name = str(spec.get("name", f"simulation_{idx}"))
        out_path = paths.plots_dir / f"{name}.png"
        try:
            _plot_series_from_spec(spec, data, out_path)
            rendered.append({
                "name": name,
                "title": str(spec.get("title", name.replace("_", " ").title())),
                "path": str(out_path.relative_to(paths.run_dir)),
            })
        except Exception:
            logger.exception("Plot generation failed")
    return rendered


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


# ---------- plot builders ----------
def _make_ifo_plots(
    paths: RunPaths,
    metrics: dict[str, Any],
    t: np.ndarray,
    I: np.ndarray,
    Q: np.ndarray,
    x_true: np.ndarray | None,
    x_b: np.ndarray,
    x_i: np.ndarray,
    fs: float,
    psd_method: str,
    nperseg: int,
    noverlap: int,
    adev_true: dict[str, Any] | None,
    adev_b: dict[str, Any],
    adev_i: dict[str, Any],
    have_simulation: bool,
) -> dict[str, Any]:
    plt.figure()
    plt.plot(t, I, label="I_meas")
    plt.plot(t, Q, label="Q_meas")
    plt.xlabel("time (s)")
    plt.ylabel("channel (a.u.)")
    plt.legend()
    raw_path = paths.plots_dir / "raw_channels.png"
    plt.tight_layout()
    plt.savefig(raw_path, dpi=160)
    plt.close()

    plt.figure()
    if x_true is not None:
        plt.plot(t, x_true, label="x_true")
    plt.plot(t, x_b, label="x_hat_baseline", alpha=0.85)
    plt.plot(t, x_i, label="x_hat_improved", alpha=0.85)
    plt.xlabel("time (s)")
    plt.ylabel("displacement (m)")
    plt.legend()
    disp_path = paths.plots_dir / "displacement.png"
    plt.tight_layout()
    plt.savefig(disp_path, dpi=160)
    plt.close()

    plt.figure()
    if x_true is not None:
        psd_true = compute_psd(x_true, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
        plt.loglog(psd_true["f_hz"][1:], psd_true["psd"][1:], label="PSD truth")
    psd_b = compute_psd(x_b, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    psd_i = compute_psd(x_i, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    plt.loglog(psd_b["f_hz"][1:], psd_b["psd"][1:], label="PSD baseline", alpha=0.85)
    plt.loglog(psd_i["f_hz"][1:], psd_i["psd"][1:], label="PSD improved", alpha=0.85)
    plt.xlabel("frequency (Hz)")
    plt.ylabel("PSD (m^2/Hz)")
    plt.legend()
    psd_path = paths.plots_dir / "psd.png"
    plt.tight_layout()
    plt.savefig(psd_path, dpi=160)
    plt.close()

    plt.figure()
    if adev_true is not None and len(np.asarray(adev_true["adev"])):
        plt.loglog(np.asarray(adev_true["taus_s"]), np.asarray(adev_true["adev"]), label="ADEV truth")
    if len(np.asarray(adev_b["adev"])):
        plt.loglog(np.asarray(adev_b["taus_s"]), np.asarray(adev_b["adev"]), label="ADEV baseline", alpha=0.85)
    if len(np.asarray(adev_i["adev"])):
        plt.loglog(np.asarray(adev_i["taus_s"]), np.asarray(adev_i["adev"]), label="ADEV improved", alpha=0.85)
    plt.xlabel("tau (s)")
    plt.ylabel("Allan deviation")
    plt.legend()
    allan_path = paths.plots_dir / "allan.png"
    plt.tight_layout()
    plt.savefig(allan_path, dpi=160)
    plt.close()

    err_path = None
    if x_true is not None:
        plt.figure()
        plt.hist(x_b - x_true, bins=40, alpha=0.7, label="baseline error")
        plt.hist(x_i - x_true, bins=40, alpha=0.7, label="improved error")
        plt.xlabel("error (m)")
        plt.ylabel("count")
        plt.legend()
        err_path = paths.plots_dir / "error_hist.png"
        plt.tight_layout()
        plt.savefig(err_path, dpi=160)
        plt.close()
    sim_plots = _make_simulation_plots(paths, {"simulation": metrics.get("simulation")}) if have_simulation else []
    return {
        "raw": str(raw_path.relative_to(paths.run_dir)),
        "displacement": str(disp_path.relative_to(paths.run_dir)),
        "psd": str(psd_path.relative_to(paths.run_dir)),
        "allan": str(allan_path.relative_to(paths.run_dir)),
        "error_hist": None if err_path is None else str(err_path.relative_to(paths.run_dir)),
        "simulation_plots": sim_plots,
    }


def _make_real_gravity_plots(
    paths: RunPaths,
    metrics: dict[str, Any],
    t_full: np.ndarray,
    x_full: np.ndarray,
    t: np.ndarray,
    x: np.ndarray,
    fs: float,
    psd_method: str,
    nperseg: int,
    noverlap: int,
    adev: dict[str, Any],
    have_simulation: bool,
) -> dict[str, Any]:
    plt.figure(figsize=(10, 4.6))
    plt.plot(t_full / 86400.0, x_full, linewidth=0.8)
    plt.xlabel("days from record start")
    plt.ylabel("gravity residual")
    plt.title("Gravity residual time series")
    raw_path = paths.plots_dir / "gravity_series.png"
    plt.tight_layout()
    plt.savefig(raw_path, dpi=160)
    plt.close()

    plt.figure(figsize=(10, 4.6))
    plt.hist(x, bins=50, alpha=0.85)
    plt.xlabel("gravity residual")
    plt.ylabel("count")
    plt.title("Gravity residual histogram (analysis segment)")
    hist_path = paths.plots_dir / "gravity_hist.png"
    plt.tight_layout()
    plt.savefig(hist_path, dpi=160)
    plt.close()

    psd = compute_psd(x, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    plt.figure(figsize=(10, 4.6))
    plt.loglog(psd["f_hz"][1:], psd["psd"][1:])
    plt.xlabel("frequency (Hz)")
    plt.ylabel("PSD")
    plt.title("Gravity residual PSD")
    psd_path = paths.plots_dir / "gravity_psd.png"
    plt.tight_layout()
    plt.savefig(psd_path, dpi=160)
    plt.close()

    plt.figure(figsize=(10, 4.6))
    plt.loglog(np.asarray(adev["taus_s"]), np.asarray(adev["adev"]))
    plt.xlabel("tau (s)")
    plt.ylabel("Allan deviation")
    plt.title("Gravity residual Allan deviation")
    allan_path = paths.plots_dir / "gravity_allan.png"
    plt.tight_layout()
    plt.savefig(allan_path, dpi=160)
    plt.close()
    sim_plots = _make_simulation_plots(paths, {"simulation": metrics.get("simulation")}) if have_simulation else []
    return {
        "raw": str(raw_path.relative_to(paths.run_dir)),
        "displacement": str(hist_path.relative_to(paths.run_dir)),
        "psd": str(psd_path.relative_to(paths.run_dir)),
        "allan": str(allan_path.relative_to(paths.run_dir)),
        "error_hist": None,
        "simulation_plots": sim_plots,
    }


# ---------- stage runners ----------
def _run_real_gravity_pipeline(cfg: dict[str, Any], cfg_text: str, paths: RunPaths, config_path: Path, *, project_root: Path | None = None) -> Path:
    grav_cfg = cfg["bench_real_gravity"]
    data = load_real_gravity(
        source_path=resolve_project_relative_path(config_path, grav_cfg["source_path"], project_root=project_root) or grav_cfg["source_path"],
        station_code=grav_cfg.get("station_code"),
        metadata_path=resolve_project_relative_path(config_path, grav_cfg.get("metadata_path"), project_root=project_root),
        segment_strategy=str(grav_cfg.get("segment_strategy", "longest_contiguous")),
    )

    x_full = np.asarray(data["gravity_residual_full"], dtype=np.float64)
    t_full = np.asarray(data["t_full"], dtype=np.float64)
    x = np.asarray(data["gravity_residual"], dtype=np.float64)
    if x.size < 3:
        raise ValueError('Dataset too small. Need at least 3 samples.')
    t = np.asarray(data["t"], dtype=np.float64)
    fs = float(data["sample_rate_hz"])
    psd_method, nperseg, noverlap, metrics_backend, allan_data_type, compare_allan_backends, comparison_backend = _stats_cfg(cfg)
    nperseg = min(max(8, nperseg), len(x))
    noverlap = min(max(1, noverlap), max(1, nperseg - 1))
    taus = _logspace_taus(duration_s=float(t[-1] - t[0]) if len(t) > 1 else 1.0, sample_rate_hz=fs)

    adev = allan_deviation_overlapping(x, fs, taus, backend=metrics_backend, data_type=allan_data_type)

    from qgrav.metrics.allan import identify_noise_type, allan_minimum
    _adev_arr = np.asarray(adev["adev"])
    _taus_arr = np.asarray(adev["taus_s"])
    noise_id = identify_noise_type(_taus_arr, _adev_arr)
    adev_min = allan_minimum(_taus_arr, _adev_arr)

    metrics: dict[str, Any] = {
        "bench_type": "real_gravity",
        "have_truth": False,
        "sample_rate_hz": fs,
        "wavelength_m": None,
        "psd_method": psd_method,
        "welch_nperseg": nperseg,
        "welch_noverlap": noverlap,
        "allan_backend_used": str(adev["backend"]),
        "allan_data_type": str(adev["data_type"]),
        "series_units": data.get("units"),
        "station_code": data.get("station_code"),
        "longitude_deg": data.get("longitude_deg"),
        "latitude_deg": data.get("latitude_deg"),
        "source_path": data.get("source_path"),
        "source_kind": data.get("source_kind"),
        "record_start": data.get("record_start"),
        "record_end": data.get("record_end"),
        "gravity_summary": {
            "mean": float(np.mean(x)),
            "std": float(np.std(x)),
            "min": float(np.min(x)),
            "max": float(np.max(x)),
            "median": float(np.median(x)),
        },
        "gap_report": data.get("gap_report", {}),
        "analysis_segment": data.get("analysis_segment", {}),
        "unit_warnings": data.get("unit_warnings", []),
        "dropped_rows": int(data.get("dropped_rows", 0)),
        "noise_identification": noise_id,
        "allan_minimum": adev_min,
        "notes": [
            "This run uses real gravimetry time-series data rather than interferometer I/Q channels.",
            "PSD and Allan deviation are computed on the selected analysis segment of the gravity residual series.",
            "If gaps exist, the default strategy is to analyze the longest contiguous segment and report the gap statistics separately.",
        ],
    }
    if compare_allan_backends:
        primary_backend = str(adev["backend"])
        if comparison_backend == primary_backend:
            comparison_backend = "custom" if primary_backend != "custom" else "allantools"
        metrics["allan_backend_comparison"] = _compare_allan_backends(
            x, fs, taus, primary_backend=primary_backend, reference_backend=comparison_backend, data_type=allan_data_type
        )

    save_dict: dict[str, np.ndarray] = {
        "t_full": t_full,
        "gravity_residual_full": x_full,
        "t": t,
        "gravity_residual": x,
        "allan_taus": np.asarray(adev["taus_s"], dtype=np.float64),
        "allan_series": np.asarray(adev["adev"], dtype=np.float64),
    }
    sim_cfg = cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
    _add_simulation(metrics, save_dict, sim_cfg)

    try:
        from qgrav.physics.systematics import systematics_summary
        lat = data.get("latitude_deg")
        metrics["systematics"] = systematics_summary(
            latitude_deg=float(lat) if lat is not None else 45.0,
        )
    except Exception:
        logger.debug("Systematics computation skipped", exc_info=True)

    metrics_jsonable = _jsonable(metrics)
    paths.metrics_path.write_text(json.dumps(metrics_jsonable, indent=2), encoding="utf-8")
    np.savez_compressed(paths.data_path, **save_dict)
    plot_paths = _make_real_gravity_plots(paths, metrics, t_full, x_full, t, x, fs, psd_method, nperseg, noverlap, adev, "simulation" in metrics)
    _write_summary(paths.summary_path, metrics_jsonable)
    _write_run_metadata(paths.run_metadata_path, cfg, metrics_jsonable)
    return build_html_report(run_dir=paths.run_dir, config_text=cfg_text, metrics=metrics_jsonable, plot_paths=plot_paths)


def _run_interferometer_pipeline(cfg: dict[str, Any], cfg_text: str, paths: RunPaths, config_path: Path, *, project_root: Path | None = None) -> Path:
    bench_cfg = cfg.get("bench", {}) if isinstance(cfg.get("bench", {}), dict) else {}
    bench_type = str(bench_cfg.get("type", "virtual")).lower().strip()
    if bench_type == "real":
        real_cfg = cfg["bench_real_ifo"]
        data = load_real_ifo_csv(
            csv_path=resolve_project_relative_path(config_path, real_cfg["csv_path"], project_root=project_root) or real_cfg["csv_path"],
            sample_rate_hz=real_cfg.get("sample_rate_hz"),
            delimiter=str(real_cfg.get("delimiter", ",")),
            has_header=bool(real_cfg.get("has_header", True)),
        )
        if real_cfg.get("sample_rate_hz") is not None:
            fs = float(real_cfg.get("sample_rate_hz"))
        elif "sample_rate_hz" in data:
            fs = float(np.asarray(data["sample_rate_hz"], dtype=np.float64).reshape(-1)[0])
        else:
            dt = np.diff(np.asarray(data["t"], dtype=np.float64))
            if len(dt) == 0:
                raise ValueError("Need at least two samples to infer sample rate for real interferometer data.")
            fs = float(1.0 / np.median(dt))
        lam = float(real_cfg.get("wavelength_m", cfg.get("bench_virtual_ifo", {}).get("wavelength_m", 1.55e-6)))
    else:
        virtual_cfg = cfg["bench_virtual_ifo"]
        data = generate_virtual_ifo(
            wavelength_m=float(virtual_cfg["wavelength_m"]),
            sample_rate_hz=float(virtual_cfg["sample_rate_hz"]),
            duration_s=float(virtual_cfg["duration_s"]),
            displacement_sines=list(virtual_cfg["displacement_sines"]),
            measurement_noise_std=float(virtual_cfg["measurement_noise_std"]),
            amplitude=float(virtual_cfg.get("amplitude", 1.0)),
            dc_offset=float(virtual_cfg.get("dc_offset", 0.0)),
            offset_drift_std_per_s=float(virtual_cfg.get("offset_drift_std_per_s", 0.0)),
            amplitude_drift_std_per_s=float(virtual_cfg.get("amplitude_drift_std_per_s", 0.0)),
            seed=int(virtual_cfg.get("seed", 0)),
        )
        fs = float(virtual_cfg["sample_rate_hz"])
        lam = float(virtual_cfg["wavelength_m"])

    t = np.asarray(data["t"], dtype=np.float64)
    I = np.asarray(data["I_meas"], dtype=np.float64)
    Q = np.asarray(data["Q_meas"], dtype=np.float64)
    x_true = np.asarray(data.get("x_true", np.full_like(t, np.nan)), dtype=np.float64)
    if len(t) < 3:
        raise ValueError("Not enough samples for interferometer analysis.")

    alg_cfg = cfg.get("algorithms", {}) if isinstance(cfg.get("algorithms", {}), dict) else {}
    imp_cfg = alg_cfg.get("improved", {}) if isinstance(alg_cfg.get("improved", {}), dict) else {}
    psd_method, nperseg, noverlap, metrics_backend, allan_data_type, compare_allan_backends, comparison_backend = _stats_cfg(cfg)
    nperseg = min(max(8, nperseg), len(t))
    noverlap = min(max(1, noverlap), max(1, nperseg - 1))

    est_base = estimate_displacement_baseline(I, Q, wavelength_m=lam)
    est_imp = estimate_displacement_improved(
        I,
        Q,
        wavelength_m=lam,
        offset_tracking_alpha=float(imp_cfg.get("offset_tracking_alpha", 0.01)),
        phase_smooth_window=int(imp_cfg.get("phase_smooth_window", 21)),
    )

    x_b = np.asarray(est_base["x_hat"], dtype=np.float64)
    x_i = np.asarray(est_imp["x_hat"], dtype=np.float64)
    n = min(len(t), len(I), len(Q), len(x_true), len(x_b), len(x_i))
    t, I, Q, x_true, x_b, x_i = t[:n], I[:n], Q[:n], x_true[:n], x_b[:n], x_i[:n]
    have_truth = bool(np.all(np.isfinite(x_true)))
    taus = _logspace_taus(duration_s=float(t[-1] - t[0]) if len(t) > 1 else 1.0, sample_rate_hz=fs)

    psd_true = compute_psd(x_true, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap) if have_truth else None
    psd_b = compute_psd(x_b, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    psd_i = compute_psd(x_i, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    adev_b = allan_deviation_overlapping(x_b, fs, taus, backend=metrics_backend, data_type=allan_data_type)
    adev_i = allan_deviation_overlapping(x_i, fs, taus, backend=metrics_backend, data_type=allan_data_type)

    from qgrav.metrics.allan import identify_noise_type, allan_minimum
    _ni_b = identify_noise_type(np.asarray(adev_b["taus_s"]), np.asarray(adev_b["adev"]))
    _ni_i = identify_noise_type(np.asarray(adev_i["taus_s"]), np.asarray(adev_i["adev"]))
    _am_b = allan_minimum(np.asarray(adev_b["taus_s"]), np.asarray(adev_b["adev"]))
    _am_i = allan_minimum(np.asarray(adev_i["taus_s"]), np.asarray(adev_i["adev"]))

    metrics: dict[str, Any] = {
        "bench_type": bench_type,
        "have_truth": have_truth,
        "sample_rate_hz": fs,
        "wavelength_m": lam,
        "psd_method": psd_method,
        "welch_nperseg": nperseg,
        "welch_noverlap": noverlap,
        "allan_backend_used": str(adev_i["backend"]),
        "allan_data_type": str(adev_i["data_type"]),
        "noise_identification_baseline": _ni_b,
        "noise_identification_improved": _ni_i,
        "allan_minimum_baseline": _am_b,
        "allan_minimum_improved": _am_i,
        "notes": [
            "Improvement percent > 0 means the improved estimator reduced the chosen error/statistic.",
            "When truth is unavailable, the report focuses on stability/spectral summaries rather than RMSE-based accuracy.",
            "In this project, AllanTools `data_type=freq` means the sampled quantity is the directly measured time series (for example displacement), not literal oscillator frequency.",
            "AISim simulation studies are saved alongside the signal-processing results. The exact interpretation depends on the selected simulation model and is documented in the report.",
        ],
    }

    if have_truth:
        adev_true = allan_deviation_overlapping(x_true, fs, taus, backend=metrics_backend, data_type=allan_data_type)
        comp_base = curve_correlation(psd_b["f_hz"], np.log10(psd_b["psd"] + 1e-30), psd_true["f_hz"], np.log10(psd_true["psd"] + 1e-30))
        comp_imp = curve_correlation(psd_i["f_hz"], np.log10(psd_i["psd"] + 1e-30), psd_true["f_hz"], np.log10(psd_true["psd"] + 1e-30))
        base_stats = compute_error_statistics(x_true, x_b)
        imp_stats = compute_error_statistics(x_true, x_i)
        metrics.update({
            "baseline": base_stats,
            "improved": imp_stats,
            "rmse_improvement_percent": improvement_percent(base_stats["rmse"], imp_stats["rmse"]),
            "mae_improvement_percent": improvement_percent(base_stats["mae"], imp_stats["mae"]),
            "psd_vs_truth_baseline": comp_base,
            "psd_vs_truth_improved": comp_imp,
        })
    else:
        adev_true = None
        metrics.update({
            "baseline": {"note": "No truth available: error statistics skipped."},
            "improved": {"note": "No truth available: error statistics skipped."},
        })

    if len(np.asarray(adev_b["adev"])) and len(np.asarray(adev_i["adev"])):
        common_tau = min(len(np.asarray(adev_b["adev"])), len(np.asarray(adev_i["adev"])))
        metrics["allan_improvement_percent_mean"] = improvement_percent(
            float(np.nanmean(np.asarray(adev_b["adev"])[:common_tau])),
            float(np.nanmean(np.asarray(adev_i["adev"])[:common_tau])),
        )

    if compare_allan_backends:
        primary_backend = str(adev_i["backend"])
        if comparison_backend == primary_backend:
            comparison_backend = "custom" if primary_backend != "custom" else "allantools"
        metrics["allan_backend_comparison"] = _compare_allan_backends(
            x_i, fs, taus, primary_backend=primary_backend, reference_backend=comparison_backend, data_type=allan_data_type
        )

    save_dict: dict[str, np.ndarray] = {
        "t": t,
        "I_meas": I,
        "Q_meas": Q,
        "x_hat_baseline": x_b,
        "x_hat_improved": x_i,
        "allan_taus": np.asarray(adev_i["taus_s"], dtype=np.float64),
        "allan_baseline": np.asarray(adev_b["adev"], dtype=np.float64),
        "allan_improved": np.asarray(adev_i["adev"], dtype=np.float64),
    }
    if have_truth:
        save_dict["x_true"] = x_true
        save_dict["allan_truth"] = np.asarray(adev_true["adev"], dtype=np.float64)
    sim_cfg = cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
    _add_simulation(metrics, save_dict, sim_cfg)

    try:
        from qgrav.physics.systematics import systematics_summary
        ifo_cfg = cfg.get("interferometer", {}) if isinstance(cfg.get("interferometer", {}), dict) else {}
        metrics["systematics"] = systematics_summary(
            interferometer_time_s=float(ifo_cfg.get("interferometer_time_s", 0.260)),
        )
    except Exception:
        logger.debug("Systematics computation skipped", exc_info=True)

    metrics_jsonable = _jsonable(metrics)
    paths.metrics_path.write_text(json.dumps(metrics_jsonable, indent=2), encoding="utf-8")
    np.savez_compressed(paths.data_path, **save_dict)
    plot_paths = _make_ifo_plots(paths, metrics, t, I, Q, x_true if have_truth else None, x_b, x_i, fs, psd_method, nperseg, noverlap, adev_true, adev_b, adev_i, "simulation" in metrics)
    _write_summary(paths.summary_path, metrics_jsonable)
    _write_run_metadata(paths.run_metadata_path, cfg, metrics_jsonable)
    return build_html_report(run_dir=paths.run_dir, config_text=cfg_text, metrics=metrics_jsonable, plot_paths=plot_paths)


def run_pipeline(config_path: Path, *, project_root: Path | None = None) -> Path:
    """Run the full qgrav pipeline from a YAML config file.

    Parameters
    ----------
    config_path:
        Path to the YAML configuration file (may be a temp file).
    project_root:
        Optional override for the project root directory. When the GUI
        materializes the config to a temp file, relative paths in the config
        cannot be resolved from the temp directory.  Passing the real project
        root ensures ``data/raw/...`` and similar paths resolve correctly.
    """
    try:
        cfg, cfg_text = load_config(config_path)
        validate_config(cfg)
        out_base = resolve_runs_dir(cfg, config_path)
        name = str(cfg.get("output", {}).get("name", "example"))
        paths = _make_run_dir(out_base, name)
        paths.config_copy.write_text(cfg_text, encoding="utf-8")

        bench_cfg = cfg.get("bench", {}) if isinstance(cfg.get("bench", {}), dict) else {}
        bench_type = str(bench_cfg.get("type", "virtual")).lower().strip()
        if bench_type == "real_gravity":
            return _run_real_gravity_pipeline(cfg, cfg_text, paths, config_path, project_root=project_root)
        return _run_interferometer_pipeline(cfg, cfg_text, paths, config_path, project_root=project_root)
    finally:
        plt.close("all")
