"""Plot generation for pipeline runs (thread-safe, OO matplotlib API)."""
from __future__ import annotations

from typing import Any

from matplotlib.figure import Figure
import numpy as np

from qgrav.metrics import compute_psd
from qgrav.pipeline._common import RunPaths
from qgrav.pipeline._simulation import _make_simulation_plots


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
    # Raw channels
    fig = Figure()
    ax = fig.add_subplot(111)
    ax.plot(t, I, label="I_meas")
    ax.plot(t, Q, label="Q_meas")
    ax.set_xlabel("time (s)")
    ax.set_ylabel("channel (a.u.)")
    ax.legend()
    raw_path = paths.plots_dir / "raw_channels.png"
    fig.tight_layout()
    fig.savefig(raw_path, dpi=160)

    # Displacement
    fig = Figure()
    ax = fig.add_subplot(111)
    if x_true is not None:
        ax.plot(t, x_true, label="x_true")
    ax.plot(t, x_b, label="x_hat_baseline", alpha=0.85)
    ax.plot(t, x_i, label="x_hat_improved", alpha=0.85)
    ax.set_xlabel("time (s)")
    ax.set_ylabel("displacement (m)")
    ax.legend()
    disp_path = paths.plots_dir / "displacement.png"
    fig.tight_layout()
    fig.savefig(disp_path, dpi=160)

    # PSD
    fig = Figure()
    ax = fig.add_subplot(111)
    if x_true is not None:
        psd_true = compute_psd(x_true, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
        ax.loglog(psd_true["f_hz"][1:], psd_true["psd"][1:], label="PSD truth")
    psd_b = compute_psd(x_b, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    psd_i = compute_psd(x_i, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    ax.loglog(psd_b["f_hz"][1:], psd_b["psd"][1:], label="PSD baseline", alpha=0.85)
    ax.loglog(psd_i["f_hz"][1:], psd_i["psd"][1:], label="PSD improved", alpha=0.85)
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("PSD (m^2/Hz)")
    ax.legend()
    psd_path = paths.plots_dir / "psd.png"
    fig.tight_layout()
    fig.savefig(psd_path, dpi=160)

    # Allan deviation
    fig = Figure()
    ax = fig.add_subplot(111)
    if adev_true is not None and len(np.asarray(adev_true["adev"])):
        ax.loglog(np.asarray(adev_true["taus_s"]), np.asarray(adev_true["adev"]), label="ADEV truth")
    if len(np.asarray(adev_b["adev"])):
        ax.loglog(np.asarray(adev_b["taus_s"]), np.asarray(adev_b["adev"]), label="ADEV baseline", alpha=0.85)
    if len(np.asarray(adev_i["adev"])):
        ax.loglog(np.asarray(adev_i["taus_s"]), np.asarray(adev_i["adev"]), label="ADEV improved", alpha=0.85)
    ax.set_xlabel("tau (s)")
    ax.set_ylabel("Allan deviation")
    ax.legend()
    allan_path = paths.plots_dir / "allan.png"
    fig.tight_layout()
    fig.savefig(allan_path, dpi=160)

    # Error histogram
    err_path = None
    if x_true is not None:
        fig = Figure()
        ax = fig.add_subplot(111)
        ax.hist(x_b - x_true, bins=40, alpha=0.7, label="baseline error")
        ax.hist(x_i - x_true, bins=40, alpha=0.7, label="improved error")
        ax.set_xlabel("error (m)")
        ax.set_ylabel("count")
        ax.legend()
        err_path = paths.plots_dir / "error_hist.png"
        fig.tight_layout()
        fig.savefig(err_path, dpi=160)

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
    # Gravity series
    fig = Figure(figsize=(10, 4.6))
    ax = fig.add_subplot(111)
    ax.plot(t_full / 86400.0, x_full, linewidth=0.8)
    ax.set_xlabel("days from record start")
    ax.set_ylabel("gravity residual")
    ax.set_title("Gravity residual time series")
    raw_path = paths.plots_dir / "gravity_series.png"
    fig.tight_layout()
    fig.savefig(raw_path, dpi=160)

    # Histogram
    fig = Figure(figsize=(10, 4.6))
    ax = fig.add_subplot(111)
    ax.hist(x, bins=50, alpha=0.85)
    ax.set_xlabel("gravity residual")
    ax.set_ylabel("count")
    ax.set_title("Gravity residual histogram (analysis segment)")
    hist_path = paths.plots_dir / "gravity_hist.png"
    fig.tight_layout()
    fig.savefig(hist_path, dpi=160)

    # PSD
    psd = compute_psd(x, fs, method=psd_method, nperseg=nperseg, noverlap=noverlap)
    fig = Figure(figsize=(10, 4.6))
    ax = fig.add_subplot(111)
    ax.loglog(psd["f_hz"][1:], psd["psd"][1:])
    ax.set_xlabel("frequency (Hz)")
    ax.set_ylabel("PSD")
    ax.set_title("Gravity residual PSD")
    psd_path = paths.plots_dir / "gravity_psd.png"
    fig.tight_layout()
    fig.savefig(psd_path, dpi=160)

    # Allan deviation
    fig = Figure(figsize=(10, 4.6))
    ax = fig.add_subplot(111)
    ax.loglog(np.asarray(adev["taus_s"]), np.asarray(adev["adev"]))
    ax.set_xlabel("tau (s)")
    ax.set_ylabel("Allan deviation")
    ax.set_title("Gravity residual Allan deviation")
    allan_path = paths.plots_dir / "gravity_allan.png"
    fig.tight_layout()
    fig.savefig(allan_path, dpi=160)

    sim_plots = _make_simulation_plots(paths, {"simulation": metrics.get("simulation")}) if have_simulation else []
    return {
        "raw": str(raw_path.relative_to(paths.run_dir)),
        "displacement": str(hist_path.relative_to(paths.run_dir)),
        "psd": str(psd_path.relative_to(paths.run_dir)),
        "allan": str(allan_path.relative_to(paths.run_dir)),
        "error_hist": None,
        "simulation_plots": sim_plots,
    }
