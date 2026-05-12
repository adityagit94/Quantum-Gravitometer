from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pathlib import Path as _PathForMPL
_MPLDIR = _PathForMPL.home() / ".qgrav_mpl"
_MPLDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPLDIR))

from matplotlib.figure import Figure
import numpy as np

from qgrav.metrics import compute_psd


def load_run_bundle(run_dir: Path) -> dict[str, Any]:
    run_dir = Path(run_dir)
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    summary = (run_dir / "SUMMARY.md").read_text(encoding="utf-8") if (run_dir / "SUMMARY.md").exists() else ""
    data = np.load(run_dir / "data.npz", allow_pickle=False)
    arrays = {key: data[key] for key in data.files}
    return {"run_dir": run_dir, "metrics": metrics, "summary": summary, "arrays": arrays}


def available_plot_kinds(bundle: dict[str, Any]) -> list[str]:
    arrays = bundle["arrays"]
    metrics = bundle["metrics"]
    bench_type = metrics.get("bench_type")
    if bench_type == "real_gravity":
        kinds = ["dashboard", "gravity_series", "histogram", "psd", "allan"]
    else:
        kinds = ["dashboard", "raw", "displacement", "psd", "allan"]
        if "x_true" in arrays:
            kinds.append("error_hist")
    sim = metrics.get("simulation", {}) if isinstance(metrics.get("simulation", {}), dict) else {}
    specs = sim.get("plot_specs", []) if isinstance(sim, dict) else []
    if isinstance(specs, list):
        for spec in specs:
            if isinstance(spec, dict):
                kinds.append(str(spec.get("name", "simulation_primary")))
    return kinds


def _new_fig(width: float = 9.2, height: float = 6.2, *, constrained: bool = False) -> Figure:
    return Figure(figsize=(width, height), dpi=110, constrained_layout=constrained)


def _plot_psd(ax, x: np.ndarray, fs: float, label: str, psd_method: str, nperseg: int, noverlap: int) -> None:
    psd = compute_psd(x, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    ax.loglog(psd["f_hz"][1:], psd["psd"][1:], label=label)


def _plot_sim_from_spec(ax, arrays: dict[str, np.ndarray], spec: dict[str, Any]) -> None:
    x = np.asarray(arrays[f"sim_{spec['x_key']}"], dtype=np.float64)
    x_scale = float(spec.get("x_scale", 1.0))
    for series in spec.get("series", []):
        y = np.asarray(arrays[f"sim_{series['key']}"], dtype=np.float64)
        label = str(series.get("label", series["key"]))
        kind = str(series.get("kind", "line"))
        if kind == "line_markers":
            ax.plot(x * x_scale, y, marker="o", markersize=2.5, linewidth=1.2, label=label)
        elif kind == "dashed":
            ax.plot(x * x_scale, y, linestyle="--", linewidth=1.3, label=label)
        else:
            ax.plot(x * x_scale, y, linewidth=1.3, label=label)
    ax.set_xlabel(str(spec.get("x_label", spec["x_key"])))
    ax.set_ylabel(str(spec.get("y_label", "value")))
    ax.set_title(str(spec.get("title", "AISim simulation")))
    if len(spec.get("series", [])) > 1:
        ax.legend()


def build_run_figure(bundle: dict[str, Any], kind: str) -> Figure:
    arrays = bundle["arrays"]
    metrics = bundle["metrics"]
    bench_type = metrics.get("bench_type")
    fs = float(metrics["sample_rate_hz"])
    psd_method = str(metrics.get("psd_method", "welch"))
    first_arr = next(iter(arrays.values()))
    nperseg = int(metrics.get("welch_nperseg", min(1024, len(first_arr))))
    noverlap = int(metrics.get("welch_noverlap", max(1, nperseg // 2)))
    sim = metrics.get("simulation", {}) if isinstance(metrics.get("simulation", {}), dict) else {}
    sim_specs = sim.get("plot_specs", []) if isinstance(sim, dict) else []

    fig = _new_fig(constrained=(kind == "dashboard"))

    if bench_type == "real_gravity":
        t_full = arrays["t_full"]
        x_full = arrays["gravity_residual_full"]
        x = arrays["gravity_residual"]
        taus = arrays["allan_taus"]
        adev = arrays["allan_series"]

        if kind == "dashboard":
            axes = fig.subplots(2, 2)
            for a in axes.flat:
                a.tick_params(labelsize=8)

            ax = axes[0, 0]
            ax.plot(t_full / 86400.0, x_full, linewidth=0.8)
            ax.set_title("Gravity series")
            ax.set_xlabel("days from start")
            ax.set_ylabel("residual")

            ax = axes[0, 1]
            ax.hist(x, bins=50, alpha=0.85)
            ax.set_title("Histogram")
            ax.set_xlabel("residual")

            ax = axes[1, 0]
            _plot_psd(ax, x, fs, "series", psd_method, nperseg, noverlap)
            ax.set_title("PSD")
            ax.set_xlabel("frequency (Hz)")
            ax.legend()

            ax = axes[1, 1]
            ax.loglog(taus, adev)
            ax.set_title("Allan deviation")
            ax.set_xlabel("tau (s)")
            return fig

        ax = fig.subplots(1, 1)
        if kind == "gravity_series":
            ax.plot(t_full / 86400.0, x_full, linewidth=0.8)
            ax.set_xlabel("days from start")
            ax.set_ylabel("gravity residual")
            ax.set_title(f"Gravity residual series ({metrics.get('station_code', 'station')})")
        elif kind == "histogram":
            ax.hist(x, bins=50, alpha=0.85)
            ax.set_xlabel("gravity residual")
            ax.set_ylabel("count")
            ax.set_title("Gravity residual histogram")
        elif kind == "psd":
            _plot_psd(ax, x, fs, "series", psd_method, nperseg, noverlap)
            ax.set_xlabel("frequency (Hz)")
            ax.set_ylabel("PSD")
            ax.set_title("Power spectral density")
            ax.legend()
        elif kind == "allan":
            ax.loglog(taus, adev)
            ax.set_xlabel("tau (s)")
            ax.set_ylabel("Allan deviation")
            ax.set_title(f"Allan deviation ({metrics.get('allan_backend_used', 'unknown')})")
        elif isinstance(sim_specs, list) and any(isinstance(spec, dict) and str(spec.get("name")) == kind for spec in sim_specs):
            spec = next(spec for spec in sim_specs if isinstance(spec, dict) and str(spec.get("name")) == kind)
            _plot_sim_from_spec(ax, arrays, spec)
        else:
            raise ValueError(f"Unsupported plot kind: {kind}")
        return fig

    t = arrays["t"]
    I = arrays["I_meas"]
    Q = arrays["Q_meas"]
    x_b = arrays["x_hat_baseline"]
    x_i = arrays["x_hat_improved"]

    if kind == "dashboard":
        axes = fig.subplots(2, 2)
        for ax in axes.flat:
            ax.tick_params(labelsize=8)
        ax = axes[0, 0]
        ax.plot(t, I, label="I")
        ax.plot(t, Q, label="Q")
        ax.set_title("Raw channels")
        ax.set_xlabel("time (s)")
        ax.legend()

        ax = axes[0, 1]
        if "x_true" in arrays:
            ax.plot(t, arrays["x_true"], label="truth")
        ax.plot(t, x_b, label="baseline", alpha=0.85)
        ax.plot(t, x_i, label="improved", alpha=0.85)
        ax.set_title("Displacement")
        ax.set_xlabel("time (s)")
        ax.legend()

        ax = axes[1, 0]
        if "x_true" in arrays:
            _plot_psd(ax, arrays["x_true"], fs, "truth", psd_method, nperseg, noverlap)
        _plot_psd(ax, x_b, fs, "baseline", psd_method, nperseg, noverlap)
        _plot_psd(ax, x_i, fs, "improved", psd_method, nperseg, noverlap)
        ax.set_title("PSD")
        ax.set_xlabel("frequency (Hz)")
        ax.legend()

        ax = axes[1, 1]
        taus = arrays["allan_taus"]
        ax.loglog(taus, arrays["allan_baseline"], label="baseline")
        ax.loglog(taus, arrays["allan_improved"], label="improved")
        if "allan_truth" in arrays:
            ax.loglog(taus, arrays["allan_truth"], label="truth")
        ax.set_title("Allan deviation")
        ax.set_xlabel("tau (s)")
        ax.legend()
        return fig

    ax = fig.subplots(1, 1)
    if kind == "raw":
        ax.plot(t, I, label="I_meas")
        ax.plot(t, Q, label="Q_meas")
        ax.set_xlabel("time (s)")
        ax.set_ylabel("channel (a.u.)")
        ax.set_title("Raw interferometer channels")
        ax.legend()
    elif kind == "displacement":
        if "x_true" in arrays:
            ax.plot(t, arrays["x_true"], label="truth")
        ax.plot(t, x_b, label="baseline", alpha=0.85)
        ax.plot(t, x_i, label="improved", alpha=0.85)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("displacement (m)")
        ax.set_title("Displacement estimate")
        ax.legend()
    elif kind == "psd":
        if "x_true" in arrays:
            _plot_psd(ax, arrays["x_true"], fs, "truth", psd_method, nperseg, noverlap)
        _plot_psd(ax, x_b, fs, "baseline", psd_method, nperseg, noverlap)
        _plot_psd(ax, x_i, fs, "improved", psd_method, nperseg, noverlap)
        ax.set_xlabel("frequency (Hz)")
        ax.set_ylabel("PSD")
        ax.set_title("Power spectral density")
        ax.legend()
    elif kind == "allan":
        taus = arrays["allan_taus"]
        ax.loglog(taus, arrays["allan_baseline"], label="baseline")
        ax.loglog(taus, arrays["allan_improved"], label="improved")
        if "allan_truth" in arrays:
            ax.loglog(taus, arrays["allan_truth"], label="truth")
        ax.set_xlabel("tau (s)")
        ax.set_ylabel("Allan deviation")
        ax.set_title(f"Allan deviation ({metrics.get('allan_backend_used', 'unknown')})")
        ax.legend()
    elif kind == "error_hist":
        if "x_true" not in arrays:
            raise ValueError("No truth data available for error histogram.")
        ax.hist(x_b - arrays["x_true"], bins=40, alpha=0.7, label="baseline")
        ax.hist(x_i - arrays["x_true"], bins=40, alpha=0.7, label="improved")
        ax.set_xlabel("error (m)")
        ax.set_ylabel("count")
        ax.set_title("Estimator error histogram")
        ax.legend()
    elif isinstance(sim_specs, list) and any(isinstance(spec, dict) and str(spec.get("name")) == kind for spec in sim_specs):
        spec = next(spec for spec in sim_specs if isinstance(spec, dict) and str(spec.get("name")) == kind)
        _plot_sim_from_spec(ax, arrays, spec)
    else:
        raise ValueError(f"Unsupported plot kind: {kind}")

    fig.tight_layout()
    return fig
