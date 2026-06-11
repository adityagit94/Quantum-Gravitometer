from __future__ import annotations

import logging
import os
import queue
import tempfile
import threading
from pathlib import Path
from pathlib import Path as _PathForMPL
from typing import Any

_MPLDIR = _PathForMPL.home() / ".qgrav_mpl"
_MPLDIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPLDIR))

import matplotlib

logger = logging.getLogger(__name__)
try:
    matplotlib.use("TkAgg")
except Exception:
    logger.exception("Failed to enable TkAgg; falling back to Agg")
    matplotlib.use("Agg")

import tkinter as tk
from tkinter import BOTH, END, X, messagebox, ttk

import yaml
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from qgrav.config import find_project_root, validate_config_structure
from qgrav.gui._tab_data_browser import DataBrowserTabMixin
from qgrav.gui._tab_editor import EditorTabMixin
from qgrav.gui._tab_guides import GuidesTabMixin
from qgrav.gui._tab_results import ResultsTabMixin
from qgrav.gui._tab_setup_run import SetupRunTabMixin
from qgrav.gui._tab_validation import ValidationTabMixin
from qgrav.gui.widgets import MetricCards, attach_tooltip
from qgrav.pipeline import run_pipeline
from qgrav.visuals import available_plot_kinds, load_run_bundle

# Threading invariant (do not break): worker threads communicate with the GUI
# exclusively via self._queue.put(...); the Tk thread polls the queue with
# root.after(150, self._poll_queue). No mixin or worker may call a Tk widget
# method from a non-Tk thread.


class QGravApp(
    SetupRunTabMixin,
    DataBrowserTabMixin,
    EditorTabMixin,
    ResultsTabMixin,
    ValidationTabMixin,
    GuidesTabMixin,
):
    def __init__(self, root: tk.Tk, default_config: Path | None = None) -> None:
        self.root = root
        self.root.title("qgrav Research Workbench")
        self.root.geometry("1460x940")
        self.root.minsize(1180, 760)

        self.config_path_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready")
        self.run_name_var = tk.StringVar(value="example")
        self.workflow_var = tk.StringVar(value="real_data")
        self.workflow_summary_var = tk.StringVar(
            value="Analyze a real gravimetry dataset and generate PSD, Allan deviation, and report outputs."
        )
        self.next_steps_var = tk.StringVar(
            value="1. Choose a dataset source.  2. Pick a station.  3. Preview data quality.  4. Run the benchmark."
        )
        self.current_context_var = tk.StringVar(value="Start by choosing a workflow in Setup.")

        self.bench_type_var = tk.StringVar(value="virtual")
        self.backend_var = tk.StringVar(value="auto")
        self.data_type_var = tk.StringVar(value="freq")
        self.psd_method_var = tk.StringVar(value="welch")
        self.sample_rate_var = tk.StringVar(value="2000")
        self.duration_var = tk.StringVar(value="5.0")
        self.real_ifo_path_var = tk.StringVar(value="")
        self.real_gravity_source_var = tk.StringVar(value="")
        self.real_gravity_station_var = tk.StringVar(value="")
        self.compare_backends_var = tk.BooleanVar(value=False)

        self.sim_enabled_var = tk.BooleanVar(value=False)
        self.sim_backend_var = tk.StringVar(value="aisim")
        self.sim_model_var = tk.StringVar(value="rabi_scan")
        self.sim_atoms_var = tk.StringVar(value="500")
        self.sim_steps_var = tk.StringVar(value="50")
        self.sim_tau_step_var = tk.StringVar(value="1e-6")
        self.sim_tau_pi_half_var = tk.StringVar(value="2.3e-5")
        self.sim_interferometer_time_var = tk.StringVar(value="0.260")
        self.sim_gravity_center_var = tk.StringVar(value="9.81")
        self.sim_gravity_span_var = tk.StringVar(value="6e-6")
        self.sim_vibration_freq_var = tk.StringVar(value="1.0")
        self.sim_vibration_amp_max_var = tk.StringVar(value="5e-8")

        # Advanced physics knobs (collapsed by default in the Setup form).
        self.sim_seed_var = tk.StringVar(value="1")
        self.sim_single_photon_detuning_var = tk.StringVar(value="0.0")
        self.sim_gravity_propagation_var = tk.BooleanVar(value=False)
        self.sim_lock_to_midfringe_var = tk.BooleanVar(value=True)
        self.sim_gravity_gradient_var = tk.StringVar(value="0.0")
        self.sim_wavefront_zernike_var = tk.StringVar(value="")
        self.sim_wavefront_radius_var = tk.StringVar(value="0.05")

        # Multi-drop measurement-cycle realism knobs.
        self.sim_n_drops_var = tk.StringVar(value="100")
        self.sim_cycle_time_var = tk.StringVar(value="1.0")
        self.sim_gravity_true_var = tk.StringVar(value="9.81")
        self.sim_detection_sigma_p_var = tk.StringVar(value="")
        self.sim_raman_phase_noise_var = tk.StringVar(value="0.0")
        self.sim_correlated_vibration_var = tk.BooleanVar(value=False)
        self.sim_seismic_model_var = tk.StringVar(value="nlnm")
        self.sim_isolation_cutoff_var = tk.StringVar(value="0.0")
        self.sim_fit_visibility_var = tk.BooleanVar(value=False)
        self.sim_projection_noise_var = tk.BooleanVar(value=False)
        self.sim_servo_enabled_var = tk.BooleanVar(value=False)
        self.sim_servo_type_var = tk.StringVar(value="integrator")
        self.sim_servo_kp_var = tk.StringVar(value="0.5")
        self.sim_servo_ki_var = tk.StringVar(value="0.1")
        self.sim_servo_kd_var = tk.StringVar(value="0.0")

        self.progress_var = tk.DoubleVar(value=0.0)
        self.plot_kind_var = tk.StringVar(value="dashboard")
        self.plot_title_var = tk.StringVar(value="No run loaded yet.")
        self.browser_dataset_var = tk.StringVar(value="")
        self.browser_station_var = tk.StringVar(value="")

        # Validation tab
        self.validation_status_var = tk.StringVar(value="Idle.")
        self.repro_atoms_var = tk.StringVar(value="")
        self.repro_drops_var = tk.StringVar(value="")
        self._validation_busy = False

        self.last_report: Path | None = None
        self.last_bundle: dict[str, Any] | None = None
        self._queue: queue.Queue[tuple[str, Any]] = queue.Queue()
        self._current_canvas: FigureCanvasTkAgg | None = None
        self._current_toolbar: NavigationToolbar2Tk | None = None
        self._browser_canvas: FigureCanvasTkAgg | None = None
        self._browser_toolbar: NavigationToolbar2Tk | None = None
        self._browser_data: dict[str, Any] | None = None
        # Multi-run Allan comparison (Results tab "Compare runs..." dialog).
        self.compare_normalize_var = tk.BooleanVar(value=False)
        self._compare_figure: Figure | None = None
        self._compare_window: tk.Toplevel | None = None
        self._compare_listbox: tk.Listbox | None = None
        self._compare_run_dirs: list[Path] = []
        self._run_in_progress = False
        self._last_temp_config_path: Path | None = None
        self._temp_config_paths: list[Path] = []
        self._project_root: Path = find_project_root(Path(__file__))
        # Stable root for bundled assets (configs/, data/, docs/, GUIDE.md).
        # Unlike _project_root (which is re-pointed at a loaded config's tree),
        # this always points at the qgrav source checkout so the Examples menu,
        # sample datasets, and Guides tab resolve correctly.
        self._asset_root: Path = find_project_root(Path(__file__))

        self._configure_style()
        self._build()
        self._bind_variable_traces()
        self._sync_workflow_sections()
        self.root.after(150, self._poll_queue)

        if default_config:
            self.config_path_var.set(str(default_config))
            self.load_config_into_editor(default_config)
        else:
            self._load_bundled_example()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError as exc:
            logger.warning("Unable to switch ttk theme to clam: %s", exc)
        style.configure("App.TFrame", background="#eef3fb")
        style.configure("Hero.TFrame", background="#16324f")
        style.configure(
            "HeroTitle.TLabel",
            background="#16324f",
            foreground="#ffffff",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "HeroSub.TLabel", background="#16324f", foreground="#d5e4ff", font=("Segoe UI", 10)
        )
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure(
            "CardTitle.TLabel",
            background="#ffffff",
            foreground="#5b6880",
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "CardValue.TLabel",
            background="#ffffff",
            foreground="#17355f",
            font=("Segoe UI", 14, "bold"),
        )
        style.configure("Section.TLabelframe", padding=8)
        style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))

    def _build(self) -> None:
        outer = ttk.Frame(self.root, style="App.TFrame", padding=12)
        outer.pack(fill=BOTH, expand=True)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(4, weight=1)

        hero = ttk.Frame(outer, style="Hero.TFrame", padding=16)
        hero.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        hero.columnconfigure(0, weight=1)
        ttk.Label(hero, text="qgrav Research Workbench", style="HeroTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            hero, text="simulation → validation → statistics → report", style="HeroSub.TLabel"
        ).grid(row=0, column=1, sticky="w", padx=16)
        ttk.Label(hero, textvariable=self.status_var, style="HeroSub.TLabel").grid(
            row=0, column=2, sticky="e", padx=16
        )

        toolbar = ttk.Frame(outer, style="App.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="Config:").grid(row=0, column=0, sticky="w")
        ttk.Entry(toolbar, textvariable=self.config_path_var).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(toolbar, text="Browse", command=self.pick_config).grid(row=0, column=2, padx=4)
        ttk.Button(toolbar, text="Load", command=self.load_current_path).grid(
            row=0, column=3, padx=4
        )
        ttk.Button(toolbar, text="Validate", command=self.validate_editor_config).grid(
            row=0, column=4, padx=4
        )
        ttk.Button(toolbar, text="Save As", command=self.save_editor_as).grid(
            row=0, column=5, padx=4
        )
        self._build_examples_menu(toolbar).grid(row=0, column=6, padx=4)
        self.run_button = ttk.Button(
            toolbar, text="Run Pipeline", style="Accent.TButton", command=self.run_async
        )
        self.run_button.grid(row=0, column=7, padx=(8, 0))

        self.progress = ttk.Progressbar(outer, variable=self.progress_var, mode="indeterminate")
        self.progress.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.cards = MetricCards(outer)
        self.cards.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        notebook = ttk.Notebook(outer)
        notebook.grid(row=4, column=0, sticky="nsew")
        self.notebook = notebook
        tab_names = [
            "Setup & Run",
            "Data Browser",
            "Config Editor",
            "Results & Visuals",
            "Validation",
            "Guides",
        ]
        tabs = [ttk.Frame(notebook, padding=10) for _ in tab_names]
        for tab, name in zip(tabs, tab_names, strict=False):
            notebook.add(tab, text=name)
        self._build_experiment_tab(tabs[0])
        self._build_data_browser_tab(tabs[1])
        self._build_editor_tab(tabs[2])
        self._build_results_tab(tabs[3])
        self._build_validation_tab(tabs[4])
        self._build_guides_tab(tabs[5])

    def _labeled_entry(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        row: int,
        column: int,
        tip: str = "",
    ) -> None:
        box = ttk.Frame(parent)
        box.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        lbl = ttk.Label(box, text=label)
        lbl.pack(anchor="w")
        entry = ttk.Entry(box, textvariable=variable)
        entry.pack(fill=X)
        if tip:
            attach_tooltip(lbl, tip)
            attach_tooltip(entry, tip)

    def _labeled_combo(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.StringVar,
        values: list[str],
        row: int,
        column: int,
        tip: str = "",
    ) -> None:
        box = ttk.Frame(parent)
        box.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        lbl = ttk.Label(box, text=label)
        lbl.pack(anchor="w")
        combo = ttk.Combobox(box, textvariable=variable, values=values, state="readonly")
        combo.pack(fill=X)
        if tip:
            attach_tooltip(lbl, tip)
            attach_tooltip(combo, tip)

    def _labeled_check(
        self,
        parent: ttk.Frame,
        label: str,
        variable: tk.BooleanVar,
        row: int,
        column: int,
        tip: str = "",
    ) -> None:
        chk = ttk.Checkbutton(parent, text=label, variable=variable)
        chk.grid(row=row, column=column, sticky="w", padx=6, pady=6)
        if tip:
            attach_tooltip(chk, tip)

    def _append_log(self, widget: tk.Text, message: str) -> None:
        widget.insert(END, message.rstrip() + "\n")
        widget.see(END)

    def _append_experiment_log(self, message: str) -> None:
        if hasattr(self, "experiment_log"):
            self.experiment_log.insert(END, message.rstrip() + "\n")
            self.experiment_log.see(END)

    def _materialize_editor_to_temp_path(self, editor_text: str) -> Path:
        fd, temp_name = tempfile.mkstemp(prefix=".qgrav_gui_", suffix=".yaml")
        os.close(fd)
        path = Path(temp_name)
        path.write_text(editor_text, encoding="utf-8")
        self._last_temp_config_path = path
        self._temp_config_paths.append(path)
        return path

    def _cleanup_temp_configs(self) -> None:
        for p in self._temp_config_paths:
            try:
                if hasattr(p, "exists") and p.exists():
                    p.unlink()
                elif isinstance(p, str):
                    if os.path.exists(p):
                        os.unlink(p)
            except Exception:
                pass
        self._temp_config_paths.clear()

    def _prepare_run_config(self) -> Path:
        editor_text = self.editor.get("1.0", END)
        cfg = yaml.safe_load(editor_text)
        if not isinstance(cfg, dict):
            raise ValueError(
                "Configuration root must be a YAML mapping (dictionary).\n\n"
                "The editor may be empty or contain invalid YAML.\n"
                "Load a config file or choose one from the Examples menu."
            )
        issues = validate_config_structure(cfg)
        if issues:
            raise ValueError("Configuration validation failed\n- " + "\n- ".join(issues))
        return self._materialize_editor_to_path(editor_text)

    def run_async(self) -> None:
        if self._run_in_progress:
            messagebox.showinfo("qgrav", "A pipeline run is already in progress.")
            return
        try:
            config_path = self._prepare_run_config()
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        self._set_running_state(True)
        self.status_var.set("Running pipeline...")
        self._append_experiment_log(f"Starting run with config: {config_path}")
        self.progress.start(10)
        threading.Thread(target=self._run_worker, args=(config_path,), daemon=True).start()

    def _run_worker(self, config_path: Path) -> None:
        try:
            report = run_pipeline(config_path, project_root=self._project_root)
            bundle = load_run_bundle(report.parent)
            self._queue.put(("success", {"report": report, "bundle": bundle}))
        except Exception as exc:
            logger.exception("Pipeline run failed")
            self._queue.put(("error", str(exc)))

    def _poll_queue(self) -> None:
        drained = False
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            if kind == "validation":
                # Independent cross-check result (separate from pipeline runs).
                self._append_log(self.validation_results, str(payload))
                self.validation_status_var.set("Done.")
                self._set_validation_busy(False)
                continue
            drained = True
            if kind == "success":
                report = Path(payload["report"])
                bundle = payload["bundle"]
                self.last_report = report
                self.last_bundle = bundle
                self.status_var.set(f"Finished: {report.name}")
                self.cards.update_from_metrics(bundle["metrics"])
                self._populate_metrics_tree(bundle["metrics"])
                self._append_log(self.result_log, f"Run complete: {report}")
                self._append_log(self.result_log, bundle.get("summary", ""))
                self._append_log(self.live_summary, f"Latest run folder: {report.parent}")
                self._append_experiment_log(f"Finished run: {report}")
                kinds = available_plot_kinds(bundle)
                self.plot_kind_combo.configure(values=kinds)
                preferred = (
                    "gravity_series"
                    if "gravity_series" in kinds
                    else ("displacement" if "displacement" in kinds else kinds[0])
                )
                self.plot_kind_var.set(preferred)
                self.current_context_var.set(
                    "Run complete. Open the report or inspect single plots first (gravity_series / displacement / PSD) before switching to dashboard."
                )
                self.refresh_plot()
            else:
                self.status_var.set("Run failed")
                messagebox.showerror("qgrav", str(payload))
                self._append_log(self.result_log, f"Run failed: {payload}")
                self._append_experiment_log(f"Run failed: {payload}")
        if drained:
            self.progress.stop()
            self.progress_var.set(0.0)
            self._set_running_state(False)
        self.root.after(150, self._poll_queue)


def main(default_config: Path | None = None) -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise RuntimeError(
            "GUI could not start. This environment may be headless or missing Tk support."
        ) from exc
    app = QGravApp(root, default_config=default_config)

    def _on_close() -> None:
        app._cleanup_temp_configs()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()
