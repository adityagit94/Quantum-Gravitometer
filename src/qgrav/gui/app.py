from __future__ import annotations

import logging
import os
import queue
import tempfile
import threading
import webbrowser
from pathlib import Path
from typing import Any

from pathlib import Path as _PathForMPL

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

import matplotlib.pyplot as plt
import numpy as np
import tkinter as tk
import yaml
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from tkinter import BOTH, END, LEFT, VERTICAL, X, filedialog, messagebox, ttk

from qgrav.bench_ifo import load_real_gravity
from qgrav.config import find_project_root, load_config, validate_config_structure
from qgrav.datasets import list_stations_in_source
from qgrav.metrics import allan_deviation_overlapping, available_allan_backends, compute_psd
from qgrav.pipeline import run_pipeline
from qgrav.visuals import available_plot_kinds, build_run_figure, load_run_bundle

from qgrav.gui.widgets import CollapsibleSection, MetricCards, ScrollableFrame, attach_tooltip


class QGravApp:
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
        style.configure("HeroTitle.TLabel", background="#16324f", foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("HeroSub.TLabel", background="#16324f", foreground="#d5e4ff", font=("Segoe UI", 10))
        style.configure("Card.TFrame", background="#ffffff", relief="flat")
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#5b6880", font=("Segoe UI", 10, "bold"))
        style.configure("CardValue.TLabel", background="#ffffff", foreground="#17355f", font=("Segoe UI", 14, "bold"))
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
        ttk.Label(hero, text="qgrav Research Workbench", style="HeroTitle.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(hero, text="simulation → validation → statistics → report", style="HeroSub.TLabel").grid(row=0, column=1, sticky="w", padx=16)
        ttk.Label(hero, textvariable=self.status_var, style="HeroSub.TLabel").grid(row=0, column=2, sticky="e", padx=16)

        toolbar = ttk.Frame(outer, style="App.TFrame")
        toolbar.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)
        ttk.Label(toolbar, text="Config:").grid(row=0, column=0, sticky="w")
        ttk.Entry(toolbar, textvariable=self.config_path_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(toolbar, text="Browse", command=self.pick_config).grid(row=0, column=2, padx=4)
        ttk.Button(toolbar, text="Load", command=self.load_current_path).grid(row=0, column=3, padx=4)
        ttk.Button(toolbar, text="Validate", command=self.validate_editor_config).grid(row=0, column=4, padx=4)
        ttk.Button(toolbar, text="Save As", command=self.save_editor_as).grid(row=0, column=5, padx=4)
        self._build_examples_menu(toolbar).grid(row=0, column=6, padx=4)
        self.run_button = ttk.Button(toolbar, text="Run Pipeline", style="Accent.TButton", command=self.run_async)
        self.run_button.grid(row=0, column=7, padx=(8, 0))

        self.progress = ttk.Progressbar(outer, variable=self.progress_var, mode="indeterminate")
        self.progress.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        self.cards = MetricCards(outer)
        self.cards.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        notebook = ttk.Notebook(outer)
        notebook.grid(row=4, column=0, sticky="nsew")
        self.notebook = notebook
        tab_names = ["Setup & Run", "Data Browser", "Config Editor", "Results & Visuals", "Validation", "Guides"]
        tabs = [ttk.Frame(notebook, padding=10) for _ in tab_names]
        for tab, name in zip(tabs, tab_names):
            notebook.add(tab, text=name)
        self._build_experiment_tab(tabs[0])
        self._build_data_browser_tab(tabs[1])
        self._build_editor_tab(tabs[2])
        self._build_results_tab(tabs[3])
        self._build_validation_tab(tabs[4])
        self._build_guides_tab(tabs[5])

    def _build_examples_menu(self, parent: ttk.Frame) -> ttk.Menubutton:
        menu_btn = ttk.Menubutton(parent, text="Examples")
        menu = tk.Menu(menu_btn, tearoff=False)
        menu.add_command(label="Default example", command=self._load_bundled_example)
        menu.add_separator()
        menu.add_command(label="AISim Rabi", command=self._load_bundled_aisim_example)
        menu.add_command(label="AISim Phase", command=self._load_bundled_aisim_phase_example)
        menu.add_command(label="AISim Gravity", command=self._load_bundled_aisim_gravity_example)
        menu.add_command(label="AISim Multi-drop (realistic ASD)", command=self._load_bundled_aisim_multi_drop_example)
        menu.add_command(label="AISim Vibration", command=self._load_bundled_aisim_vibration_example)
        menu.add_separator()
        menu.add_command(label="Real gravity example", command=self._load_bundled_real_gravity_example)
        menu_btn["menu"] = menu
        return menu_btn

    def _build_experiment_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        pane = ttk.Panedwindow(parent, orient="horizontal")
        pane.grid(row=0, column=0, sticky="nsew")

        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=2)
        pane.add(right, weight=3)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=2)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        quick = ttk.Labelframe(left, text="Setup controls", style="Section.TLabelframe")
        quick.grid(row=0, column=0, sticky="nsew", pady=4)
        scroller = ScrollableFrame(quick)
        scroller.pack(fill=BOTH, expand=True)
        controls_parent = scroller.inner
        controls_parent.columnconfigure(0, weight=1)

        self.workflow_frame = ttk.Labelframe(controls_parent, text="Start Here", style="Section.TLabelframe")
        self.workflow_frame.pack(fill=X, expand=False, pady=(0, 10))
        ttk.Label(
            self.workflow_frame,
            text="Choose a workflow first. The interface will show only the controls that matter for that task.",
            wraplength=430,
        ).pack(anchor="w", padx=6, pady=(2, 6))
        wf_row = ttk.Frame(self.workflow_frame)
        wf_row.pack(fill=X, padx=6)
        ttk.Label(wf_row, text="Workflow").pack(side=LEFT)
        ttk.Combobox(
            wf_row,
            textvariable=self.workflow_var,
            values=["real_data", "synthetic", "advanced"],
            state="readonly",
            width=18,
        ).pack(side=LEFT, padx=8)
        ttk.Label(self.workflow_frame, textvariable=self.workflow_summary_var, wraplength=430, foreground="#334e68").pack(anchor="w", padx=6, pady=(8, 2))
        ttk.Label(self.workflow_frame, textvariable=self.next_steps_var, wraplength=430, foreground="#5b6880").pack(anchor="w", padx=6, pady=(0, 2))

        self.analysis_frame = ttk.Labelframe(controls_parent, text="Analysis settings", style="Section.TLabelframe")
        self.analysis_frame.pack(fill=X, expand=False, pady=(0, 10))
        ttk.Label(
            self.analysis_frame,
            text="These settings affect how spectra and stability metrics are computed.",
            wraplength=430,
            foreground="#5b6880",
        ).pack(anchor="w", padx=6, pady=(2, 6))
        analysis_fields = ttk.Frame(self.analysis_frame)
        analysis_fields.pack(fill=X, expand=True)
        for col in range(2):
            analysis_fields.columnconfigure(col, weight=1)
        self._labeled_entry(analysis_fields, "Run name", self.run_name_var, 0, 0)
        self._labeled_combo(analysis_fields, "Allan backend", self.backend_var, ["auto", "custom"] + [b for b in available_allan_backends() if b not in {"custom"}], 0, 1)
        self._labeled_combo(analysis_fields, "Allan data type", self.data_type_var, ["freq", "phase"], 1, 0)
        self._labeled_combo(analysis_fields, "PSD method", self.psd_method_var, ["welch", "periodogram"], 1, 1)
        ttk.Checkbutton(analysis_fields, text="Compare Allan backends", variable=self.compare_backends_var).grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Label(
            analysis_fields,
            text="Use Allantools/Welch for report-quality real-data analysis. Periodogram/custom are mainly for debugging or comparison.",
            wraplength=430,
            foreground="#5b6880",
        ).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        self.real_data_frame = ttk.Labelframe(controls_parent, text="Real-data input", style="Section.TLabelframe")
        self.real_data_frame.pack(fill=X, expand=False, pady=(0, 10))
        real_top = ttk.Frame(self.real_data_frame)
        real_top.pack(fill=X, expand=True)
        for col in range(2):
            real_top.columnconfigure(col, weight=1)
        self._labeled_combo(real_top, "Bench type", self.bench_type_var, ["real_gravity", "real"], 0, 0)
        ttk.Label(
            real_top,
            text="Use real_gravity for IGETS/Larzac-style gravity residual analysis. Use real for interferometer-style CSV data.",
            wraplength=430,
            foreground="#5b6880",
        ).grid(row=0, column=1, sticky="w", padx=6, pady=6)

        self.real_gravity_subframe = ttk.Frame(self.real_data_frame)
        self.real_gravity_subframe.pack(fill=X, expand=False, pady=(6, 0))
        rg_fields = ttk.Frame(self.real_gravity_subframe)
        rg_fields.pack(fill=X, expand=True)
        for col in range(2):
            rg_fields.columnconfigure(col, weight=1)
        self._labeled_entry(rg_fields, "Gravity source (.zip/.ggp/dir/csv)", self.real_gravity_source_var, 0, 0)
        self._labeled_entry(rg_fields, "Gravity station code", self.real_gravity_station_var, 0, 1)
        ttk.Button(self.real_gravity_subframe, text="Use browser selection", command=self._use_browser_selection_for_gravity).pack(anchor="w", padx=6, pady=(4, 0))

        self.real_ifo_subframe = ttk.Frame(self.real_data_frame)
        rifo_fields = ttk.Frame(self.real_ifo_subframe)
        rifo_fields.pack(fill=X, expand=True)
        for col in range(2):
            rifo_fields.columnconfigure(col, weight=1)
        self._labeled_entry(rifo_fields, "Real IFO CSV", self.real_ifo_path_var, 0, 0)
        self._labeled_entry(rifo_fields, "Sample rate (Hz)", self.sample_rate_var, 0, 1)
        ttk.Label(
            self.real_ifo_subframe,
            text="Use this only for interferometer-style CSV data with time/value channels.",
            wraplength=430,
            foreground="#5b6880",
        ).pack(anchor="w", padx=6, pady=(4, 0))

        self.synthetic_frame = ttk.Labelframe(controls_parent, text="Synthetic gravimeter study", style="Section.TLabelframe")
        self.synthetic_frame.pack(fill=X, expand=False, pady=(0, 10))
        ttk.Label(
            self.synthetic_frame,
            text="These controls are only relevant when you are running an AISim-backed or hybrid gravimeter study.",
            wraplength=430,
        ).pack(anchor="w", padx=6, pady=(2, 6))
        sim_top = ttk.Frame(self.synthetic_frame)
        sim_top.pack(fill=X, expand=True)
        for col in range(2):
            sim_top.columnconfigure(col, weight=1)
        en = ttk.Checkbutton(sim_top, text="Enable AISim module", variable=self.sim_enabled_var)
        en.grid(row=0, column=0, sticky="w", padx=6, pady=6)
        attach_tooltip(en, "Turn the synthetic atom-interferometer engine on. When off, the pipeline only does data analysis.")
        self._labeled_combo(sim_top, "Simulation backend", self.sim_backend_var, ["aisim"], 0, 1,
                            tip="AISim is the vendored semiclassical atom-interferometer backend (the only backend currently shipped).")
        self._labeled_combo(
            sim_top, "Study model", self.sim_model_var,
            ["rabi_scan", "mach_zehnder_phase_scan", "gravity_sweep", "multi_drop_cycle", "vibration_sensitivity_sweep"],
            1, 0,
            tip=(
                "rabi_scan: pulse-area calibration.\n"
                "mach_zehnder_phase_scan: a single 3-pulse fringe.\n"
                "gravity_sweep: fringe phase vs g (emergent-gravity check).\n"
                "multi_drop_cycle: realistic repeated drops with noise + servo -> ASD/Allan (the flagship model).\n"
                "vibration_sensitivity_sweep: contrast vs reference-mirror vibration."
            ),
        )
        self._labeled_entry(sim_top, "Atoms", self.sim_atoms_var, 1, 1,
                            tip="Number of atoms in the Monte-Carlo ensemble. More atoms = lower projection-noise floor (sigma_g ~ 1/sqrt(N)) but slower.")
        self._labeled_entry(sim_top, "Steps / points", self.sim_steps_var, 2, 0,
                            tip="Number of scan points (Rabi tau steps, phase points, or gravity points). Ignored by multi_drop_cycle (use 'drops per cycle' below).")
        self._labeled_entry(sim_top, "π/2 pulse duration (s)", self.sim_tau_pi_half_var, 2, 1,
                            tip="Duration of a pi/2 Raman pulse. Freier 2016 uses ~17 us; the default is 23 us.")
        self._labeled_entry(sim_top, "Tau step (s)", self.sim_tau_step_var, 3, 0,
                            tip="Rabi-scan pulse-duration increment per step (rabi_scan only).")
        self._labeled_entry(sim_top, "Interferometer T (s)", self.sim_interferometer_time_var, 3, 1,
                            tip="Pulse-separation time T. Phase scales as k_eff*g*T^2, so sensitivity grows as T^2. Freier 2016 uses 260 ms.")
        self._labeled_entry(sim_top, "Gravity center (m/s²)", self.sim_gravity_center_var, 4, 0,
                            tip="Central gravity value for a gravity_sweep, or the reference g for vibration studies.")
        self._labeled_entry(sim_top, "Gravity span (m/s²)", self.sim_gravity_span_var, 4, 1,
                            tip="Full width of the gravity_sweep around the centre value (e.g. 6e-6 m/s^2).")
        self._labeled_entry(sim_top, "Vibration freq (Hz)", self.sim_vibration_freq_var, 5, 0,
                            tip="Reference-mirror vibration frequency (vibration_sensitivity_sweep only).")
        self._labeled_entry(sim_top, "Max vibration amp (m)", self.sim_vibration_amp_max_var, 5, 1,
                            tip="Largest mirror-vibration amplitude in the sweep (vibration_sensitivity_sweep only).")

        # --- Advanced physics (collapsed by default) ---------------------
        adv = CollapsibleSection(
            self.synthetic_frame,
            "Advanced physics  (detuning · wavefront · propagation)",
            subtitle="Optional. Apply to mach_zehnder_phase_scan, gravity_sweep, and multi_drop_cycle. Defaults reproduce the simple analytical model.",
        )
        adv.pack(fill=X, expand=True, pady=(8, 0))
        adv_fields = adv.body
        for col in range(2):
            adv_fields.columnconfigure(col, weight=1)
        self._labeled_entry(adv_fields, "Random seed", self.sim_seed_var, 0, 0,
                            tip="Seed for the atom-ensemble RNG. Fix it for reproducible runs.")
        self._labeled_entry(adv_fields, "Single-photon detuning (Hz)", self.sim_single_photon_detuning_var, 0, 1,
                            tip="Raman single-photon detuning Delta. Sets the AC-Stark / light shift. Freier 2016 uses about -700 MHz.")
        self._labeled_check(adv_fields, "Gravity propagation (ballistic)", self.sim_gravity_propagation_var, 1, 0,
                            tip="If on, the phase emerges from real ballistic free-fall + chirped laser instead of being injected analytically. The honest 'emergent gravity' path.")
        self._labeled_check(adv_fields, "Lock to mid-fringe", self.sim_lock_to_midfringe_var, 1, 1,
                            tip="gravity_sweep only: bias the interferometer to the steepest, most sensitive point of the fringe.")
        self._labeled_entry(adv_fields, "Gravity gradient (1/m)", self.sim_gravity_gradient_var, 2, 0,
                            tip="Vertical gravity gradient d g / d z (e.g. -3.1e-6 s^-2). 0 disables it.")
        self._labeled_entry(adv_fields, "Wavefront Zernike coeffs", self.sim_wavefront_zernike_var, 2, 1,
                            tip="Comma-separated Zernike coefficients in metres of wavefront error, e.g. '0,0,0,5e-9' (defocus). Blank = flat wavefront.")
        self._labeled_entry(adv_fields, "Wavefront radius (m)", self.sim_wavefront_radius_var, 3, 0,
                            tip="Beam radius over which the Zernike wavefront is normalised (default 0.05 m).")

        # --- Multi-drop noise budget (collapsed by default) --------------
        noise = CollapsibleSection(
            self.synthetic_frame,
            "Multi-drop noise budget & servo  (multi_drop_cycle)",
            subtitle="Used only by multi_drop_cycle. These knobs set the realistic per-shot noise and the fringe-lock servo that turn a fringe into an ASD/Allan curve.",
        )
        noise.pack(fill=X, expand=True, pady=(8, 0))
        nf = noise.body
        for col in range(2):
            nf.columnconfigure(col, weight=1)
        self._labeled_entry(nf, "Drops per cycle", self.sim_n_drops_var, 0, 0,
                            tip="Number of repeated measurement drops. The simulated ASD/Allan curve is built from this time series.")
        self._labeled_entry(nf, "Cycle time (s)", self.sim_cycle_time_var, 0, 1,
                            tip="Time per drop (1/repetition-rate). Sets the time axis for ASD and Allan deviation. Freier 2016: 1.5 s.")
        self._labeled_entry(nf, "True gravity (m/s²)", self.sim_gravity_true_var, 1, 0,
                            tip="The ground-truth g the simulated instrument is trying to recover.")
        self._labeled_entry(nf, "Detection sigma_p", self.sim_detection_sigma_p_var, 1, 1,
                            tip="Per-shot detection noise on the excited fraction P (technical/electronic). Blank = use shot-noise from atom number only. Freier 2016: ~6e-3.")
        self._labeled_entry(nf, "Raman phase noise (rad)", self.sim_raman_phase_noise_var, 2, 0,
                            tip="Per-shot laser/Raman + residual-vibration phase noise (rad RMS), added directly to the interferometer phase.")
        self._labeled_check(nf, "Correlated seismic vibration", self.sim_correlated_vibration_var, 2, 1,
                            tip="If on, inject a time-correlated seismic vibration series (Peterson model) instead of white phase noise.")
        self._labeled_combo(nf, "Seismic model", self.sim_seismic_model_var, ["nlnm", "nhnm"], 3, 0,
                            tip="Peterson New Low / High Noise Model for the correlated seismic background.")
        self._labeled_entry(nf, "Isolation cutoff (Hz)", self.sim_isolation_cutoff_var, 3, 1,
                            tip="Vibration-isolation corner frequency. Vibration below this is suppressed. 0 = no isolation.")
        self._labeled_check(nf, "Fit fringe visibility", self.sim_fit_visibility_var, 4, 0,
                            tip="Fit the contrast V from the simulated data and use the same V for the P->g inversion (keeps the noise budget self-consistent).")
        self._labeled_check(nf, "Enable fringe-lock servo", self.sim_servo_enabled_var, 4, 1,
                            tip="Close a feedback loop that steers each drop back to mid-fringe (as a real gravimeter does).")
        self._labeled_combo(nf, "Servo type", self.sim_servo_type_var, ["integrator", "pid"], 5, 0,
                            tip="integrator: simple I servo. pid: full proportional-integral-derivative with anti-windup.")
        servo_gains = ttk.Frame(nf)
        servo_gains.grid(row=6, column=0, columnspan=2, sticky="ew")
        for col in range(3):
            servo_gains.columnconfigure(col, weight=1)
        self._labeled_entry(servo_gains, "Servo kp", self.sim_servo_kp_var, 0, 0, tip="Proportional gain (pid).")
        self._labeled_entry(servo_gains, "Servo ki", self.sim_servo_ki_var, 0, 1, tip="Integral gain (integrator and pid).")
        self._labeled_entry(servo_gains, "Servo kd", self.sim_servo_kd_var, 0, 2, tip="Derivative gain (pid).")

        self.workflow_compare_note = ttk.Labelframe(controls_parent, text="Advanced mode", style="Section.TLabelframe")
        self.workflow_compare_note.pack(fill=X, expand=False, pady=(0, 10))
        ttk.Label(
            self.workflow_compare_note,
            text="Use this mode when you want to edit YAML directly or inspect previous runs. Compare plots and metrics from the Results tab after a run.",
            wraplength=430,
            foreground="#5b6880",
        ).pack(anchor="w", padx=6, pady=6)

        actions = ttk.Labelframe(controls_parent, text="Actions", style="Section.TLabelframe")
        actions.pack(fill=X, expand=False, pady=(0, 10))
        ttk.Label(actions, textvariable=self.current_context_var, wraplength=430, foreground="#5b6880").pack(anchor="w", padx=6, pady=(2, 6))
        btns = ttk.Frame(actions)
        btns.pack(fill=X, padx=6, pady=(0, 4))
        ttk.Button(btns, text="Pull from editor", command=self.sync_controls_from_editor).pack(side=LEFT, padx=(0, 6))
        ttk.Button(btns, text="Apply controls to editor", command=self.apply_quick_controls_to_editor).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="Open report", command=self.open_report).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="Open run folder", command=self.open_run_folder).pack(side=LEFT, padx=6)

        summary = ttk.Labelframe(right, text="Recommended next steps & run summary", style="Section.TLabelframe")
        summary.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        summary.rowconfigure(1, weight=1)
        summary.columnconfigure(0, weight=1)
        ttk.Label(summary, textvariable=self.next_steps_var, wraplength=760, foreground="#334e68").grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 8))
        summary_frame = ttk.Frame(summary)
        summary_frame.grid(row=1, column=0, sticky="nsew")
        summary_frame.rowconfigure(0, weight=1)
        summary_frame.columnconfigure(0, weight=1)
        self.live_summary = tk.Text(summary_frame, wrap="word", height=24)
        self.live_summary.grid(row=0, column=0, sticky="nsew")
        summary_scroll = ttk.Scrollbar(summary_frame, orient=VERTICAL, command=self.live_summary.yview)
        summary_scroll.grid(row=0, column=1, sticky="ns")
        self.live_summary.configure(yscrollcommand=summary_scroll.set)
        self.live_summary.insert("1.0", "Load a config, choose a workflow, then run the pipeline.\n")

        runlog = ttk.Labelframe(right, text="Live run log", style="Section.TLabelframe")
        runlog.grid(row=1, column=0, sticky="nsew")
        runlog.rowconfigure(0, weight=1)
        runlog.columnconfigure(0, weight=1)
        self.experiment_log = tk.Text(runlog, wrap="word", height=10)
        self.experiment_log.grid(row=0, column=0, sticky="nsew")
        runlog_scroll = ttk.Scrollbar(runlog, orient=VERTICAL, command=self.experiment_log.yview)
        runlog_scroll.grid(row=0, column=1, sticky="ns")
        self.experiment_log.configure(yscrollcommand=runlog_scroll.set)

    def _build_data_browser_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        pane = ttk.Panedwindow(parent, orient="horizontal")
        pane.grid(row=0, column=0, sticky="nsew")
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=2)
        pane.add(right, weight=3)
        left.rowconfigure(1, weight=1)
        left.rowconfigure(2, weight=1)
        left.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        right.columnconfigure(0, weight=1)

        top = ttk.Labelframe(left, text="Dataset source", style="Section.TLabelframe")
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        row = ttk.Frame(top)
        row.pack(fill=X, expand=True)
        row.columnconfigure(1, weight=1)
        ttk.Label(row, text="Source").grid(row=0, column=0, sticky="w")
        ttk.Entry(row, textvariable=self.browser_dataset_var).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(row, text="Browse", command=self._browse_dataset_source).grid(row=0, column=2, padx=4)
        ttk.Button(row, text="Scan", command=self.scan_dataset_source).grid(row=0, column=3, padx=4)
        ttk.Button(row, text="Use sample", command=self._load_sample_dataset).grid(row=0, column=4, padx=4)
        ttk.Label(
            top,
            text="Use this tab to inspect available stations before filling the Setup form. For IGETS/Larzac data, scan the folder first, then preview one station.",
            wraplength=520,
            foreground="#5b6880",
        ).pack(anchor="w", padx=6, pady=(6, 2))

        stations_box = ttk.Labelframe(left, text="Available stations", style="Section.TLabelframe")
        stations_box.grid(row=1, column=0, sticky="nsew")
        stations_box.rowconfigure(0, weight=1)
        stations_box.columnconfigure(0, weight=1)
        tree_frame = ttk.Frame(stations_box)
        tree_frame.grid(row=0, column=0, sticky="nsew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)
        self.station_tree = ttk.Treeview(tree_frame, columns=("lon", "lat"), show="tree headings", height=18)
        self.station_tree.heading("#0", text="Station")
        self.station_tree.heading("lon", text="Longitude")
        self.station_tree.heading("lat", text="Latitude")
        self.station_tree.column("#0", width=110, stretch=True)
        self.station_tree.column("lon", width=90)
        self.station_tree.column("lat", width=90)
        self.station_tree.grid(row=0, column=0, sticky="nsew")
        station_tree_scroll = ttk.Scrollbar(tree_frame, orient=VERTICAL, command=self.station_tree.yview)
        station_tree_scroll.grid(row=0, column=1, sticky="ns")
        self.station_tree.configure(yscrollcommand=station_tree_scroll.set)
        self.station_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_station_selected())

        info_box = ttk.Labelframe(left, text="Station details", style="Section.TLabelframe")
        info_box.grid(row=2, column=0, sticky="nsew", pady=(8, 0))
        info_box.rowconfigure(0, weight=1)
        info_box.columnconfigure(0, weight=1)
        info_frame = ttk.Frame(info_box)
        info_frame.grid(row=0, column=0, sticky="nsew")
        info_frame.rowconfigure(0, weight=1)
        info_frame.columnconfigure(0, weight=1)
        self.station_info = tk.Text(info_frame, wrap="word", height=12)
        self.station_info.grid(row=0, column=0, sticky="nsew")
        station_info_scroll = ttk.Scrollbar(info_frame, orient=VERTICAL, command=self.station_info.yview)
        station_info_scroll.grid(row=0, column=1, sticky="ns")
        self.station_info.configure(yscrollcommand=station_info_scroll.set)
        controls = ttk.Frame(info_box)
        controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(controls, text="Preview selected", command=self.preview_selected_station).pack(side=LEFT, padx=4)
        ttk.Button(controls, text="Create config", command=self.create_real_gravity_config_from_selection).pack(side=LEFT, padx=4)
        ttk.Button(controls, text="Use in Setup", command=self._use_browser_selection_for_gravity).pack(side=LEFT, padx=4)

        preview = ttk.Labelframe(right, text="Station preview", style="Section.TLabelframe")
        preview.grid(row=0, column=0, sticky="nsew")
        preview.rowconfigure(2, weight=1)
        preview.columnconfigure(0, weight=1)
        ttk.Label(
            preview,
            text="Preview one station before running the full pipeline. This view is for data quality inspection only.",
            foreground="#5b6880",
            wraplength=760,
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 6))
        self.browser_toolbar_frame = ttk.Frame(preview)
        self.browser_toolbar_frame.grid(row=1, column=0, sticky="ew")
        self.browser_plot_frame = ttk.Frame(preview)
        self.browser_plot_frame.grid(row=2, column=0, sticky="nsew")
        self.browser_plot_frame.rowconfigure(0, weight=1)
        self.browser_plot_frame.columnconfigure(0, weight=1)

    def _build_editor_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        frame = ttk.Labelframe(parent, text="YAML config editor", style="Section.TLabelframe")
        frame.grid(row=0, column=0, sticky="nsew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.editor = tk.Text(frame, wrap="none")
        self.editor.grid(row=0, column=0, sticky="nsew")
        yscroll = ttk.Scrollbar(frame, orient=VERTICAL, command=self.editor.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.editor.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        self.editor.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)

    def _build_results_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)
        top_pane = ttk.Panedwindow(parent, orient="horizontal")
        top_pane.grid(row=0, column=0, sticky="nsew")
        left = ttk.Frame(top_pane)
        right = ttk.Frame(top_pane)
        top_pane.add(left, weight=2)
        top_pane.add(right, weight=4)
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        metrics_box = ttk.Labelframe(left, text="Metrics browser", style="Section.TLabelframe")
        metrics_box.grid(row=0, column=0, sticky="nsew")
        metrics_box.rowconfigure(2, weight=1)
        metrics_box.columnconfigure(0, weight=1)
        artifact_bar = ttk.Frame(metrics_box)
        artifact_bar.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        for label, cmd in [("Open HTML", self.open_report), ("Run folder", self.open_run_folder), ("Metrics JSON", self.open_metrics_file), ("Summary", self.open_summary_file)]:
            ttk.Button(artifact_bar, text=label, command=cmd).pack(side=LEFT, padx=6)
        ttk.Label(
            metrics_box,
            text="Use this panel to inspect run outputs. For real-data work, look first at station info, PSD, and Allan deviation.",
            foreground="#5b6880",
            wraplength=360,
        ).grid(row=1, column=0, sticky="ew", padx=6, pady=(0, 6))
        metrics_frame = ttk.Frame(metrics_box)
        metrics_frame.grid(row=2, column=0, sticky="nsew")
        metrics_frame.rowconfigure(0, weight=1)
        metrics_frame.columnconfigure(0, weight=1)
        self.metrics_tree = ttk.Treeview(metrics_frame, columns=("value",), show="tree headings")
        self.metrics_tree.heading("#0", text="Metric")
        self.metrics_tree.heading("value", text="Value")
        self.metrics_tree.column("#0", width=220, stretch=True)
        self.metrics_tree.column("value", width=220, stretch=True)
        self.metrics_tree.grid(row=0, column=0, sticky="nsew")
        metrics_scroll_y = ttk.Scrollbar(metrics_frame, orient=VERTICAL, command=self.metrics_tree.yview)
        metrics_scroll_y.grid(row=0, column=1, sticky="ns")
        metrics_scroll_x = ttk.Scrollbar(metrics_frame, orient="horizontal", command=self.metrics_tree.xview)
        metrics_scroll_x.grid(row=1, column=0, sticky="ew")
        self.metrics_tree.configure(yscrollcommand=metrics_scroll_y.set, xscrollcommand=metrics_scroll_x.set)

        visuals_box = ttk.Labelframe(right, text="Interactive visuals", style="Section.TLabelframe")
        visuals_box.grid(row=0, column=0, sticky="nsew")
        visuals_box.rowconfigure(3, weight=1)
        visuals_box.columnconfigure(0, weight=1)
        ttk.Label(visuals_box, textvariable=self.plot_title_var, foreground="#5b6880", wraplength=760).grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 4))
        top = ttk.Frame(visuals_box)
        top.grid(row=1, column=0, sticky="ew", padx=6)
        ttk.Label(top, text="Plot:").pack(side=LEFT)
        self.plot_kind_combo = ttk.Combobox(top, textvariable=self.plot_kind_var, values=["dashboard"], state="readonly", width=22)
        self.plot_kind_combo.pack(side=LEFT, padx=8)
        self.plot_kind_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_plot())
        ttk.Button(top, text="Refresh", command=self.refresh_plot).pack(side=LEFT, padx=4)
        self.plot_toolbar_frame = ttk.Frame(visuals_box)
        self.plot_toolbar_frame.grid(row=2, column=0, sticky="ew", padx=6, pady=(4, 4))
        self.plot_frame = ttk.Frame(visuals_box)
        self.plot_frame.grid(row=3, column=0, sticky="nsew", padx=6, pady=(0, 6))
        self.plot_frame.rowconfigure(0, weight=1)
        self.plot_frame.columnconfigure(0, weight=1)

        log_box = ttk.Labelframe(parent, text="Run log", style="Section.TLabelframe")
        log_box.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        log_box.rowconfigure(1, weight=1)
        log_box.columnconfigure(0, weight=1)
        ttk.Label(
            log_box,
            text="This log explains what happened during the run and highlights comparison/backend notes.",
            foreground="#5b6880",
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 4))
        result_frame = ttk.Frame(log_box)
        result_frame.grid(row=1, column=0, sticky="nsew")
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)
        self.result_log = tk.Text(result_frame, wrap="word", height=10)
        self.result_log.grid(row=0, column=0, sticky="nsew")
        result_scroll = ttk.Scrollbar(result_frame, orient=VERTICAL, command=self.result_log.yview)
        result_scroll.grid(row=0, column=1, sticky="ns")
        self.result_log.configure(yscrollcommand=result_scroll.set)

    # ------------------------------------------------------------------
    # Validation tab
    # ------------------------------------------------------------------
    _REPRODUCTIONS = [
        ("freier_2016", "Freier 2016 — GAIN (Berlin)", "PRIMARY regression target"),
        ("hu_2013", "Hu 2013 — HUST fountain", "secondary"),
        ("menoret_2018", "Ménoret 2018 — AQG (Muquans)", "secondary"),
        ("xu_2022", "Xu 2022 — CMI / NIM comparison", "secondary"),
        ("wu_2019", "Wu 2019 — Stanford 10 m", "secondary"),
    ]

    def _build_validation_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        pane = ttk.Panedwindow(parent, orient="horizontal")
        pane.grid(row=0, column=0, sticky="nsew")
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=2)
        pane.add(right, weight=3)
        left.rowconfigure(1, weight=2)
        left.rowconfigure(3, weight=1)
        left.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=2)
        right.rowconfigure(3, weight=1)
        right.columnconfigure(0, weight=1)

        # --- LEFT: published reference library ---------------------------
        ttk.Label(
            left,
            text="qgrav ships a registry of measured values from published atom-gravimeter papers. "
                 "These are the numbers the automated regression suite checks against.",
            wraplength=420,
            foreground="#334e68",
        ).grid(row=0, column=0, sticky="ew", padx=4, pady=(2, 6))

        refs_box = ttk.Labelframe(left, text="Published reference library", style="Section.TLabelframe")
        refs_box.grid(row=1, column=0, sticky="nsew")
        refs_box.rowconfigure(0, weight=1)
        refs_box.columnconfigure(0, weight=1)
        self.refs_tree = ttk.Treeview(refs_box, columns=("value", "unit", "year"), show="tree headings", height=12)
        self.refs_tree.heading("#0", text="Key")
        self.refs_tree.heading("value", text="Value")
        self.refs_tree.heading("unit", text="Unit")
        self.refs_tree.heading("year", text="Year")
        self.refs_tree.column("#0", width=180, stretch=True)
        self.refs_tree.column("value", width=90)
        self.refs_tree.column("unit", width=120)
        self.refs_tree.column("year", width=48, anchor="center")
        self.refs_tree.grid(row=0, column=0, sticky="nsew")
        refs_scroll = ttk.Scrollbar(refs_box, orient=VERTICAL, command=self.refs_tree.yview)
        refs_scroll.grid(row=0, column=1, sticky="ns")
        self.refs_tree.configure(yscrollcommand=refs_scroll.set)
        self.refs_tree.bind("<<TreeviewSelect>>", lambda _e: self._on_reference_selected())

        ttk.Label(left, text="Reference details", foreground="#5b6880").grid(row=2, column=0, sticky="w", padx=4, pady=(8, 0))
        detail_frame = ttk.Frame(left)
        detail_frame.grid(row=3, column=0, sticky="nsew")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)
        self.ref_detail = tk.Text(detail_frame, wrap="word", height=7)
        self.ref_detail.grid(row=0, column=0, sticky="nsew")
        ref_detail_scroll = ttk.Scrollbar(detail_frame, orient=VERTICAL, command=self.ref_detail.yview)
        ref_detail_scroll.grid(row=0, column=1, sticky="ns")
        self.ref_detail.configure(yscrollcommand=ref_detail_scroll.set, state="disabled")

        # --- RIGHT: reproductions + QuTiP cross-check --------------------
        repro_box = ttk.Labelframe(right, text="Reproduce a published measurement (one click)", style="Section.TLabelframe")
        repro_box.grid(row=0, column=0, sticky="nsew", pady=(0, 6))
        repro_box.columnconfigure(0, weight=1)
        ttk.Label(
            repro_box,
            text="Each row builds a ready-to-run multi_drop_cycle config from that paper's documented "
                 "parameters and noise budget. 'Predicted' is qgrav's analytic short-term ASD; 'Published' "
                 "is the paper's reported value. Select a row, then load it into the editor and press Run.",
            wraplength=720,
            foreground="#5b6880",
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(2, 6))

        repro_tree_frame = ttk.Frame(repro_box)
        repro_tree_frame.grid(row=1, column=0, sticky="nsew", padx=6)
        repro_tree_frame.columnconfigure(0, weight=1)
        self.repro_tree = ttk.Treeview(
            repro_tree_frame,
            columns=("published", "predicted", "ratio", "status"),
            show="tree headings",
            height=6,
        )
        self.repro_tree.heading("#0", text="Paper")
        self.repro_tree.heading("published", text="Published ASD")
        self.repro_tree.heading("predicted", text="Predicted ASD")
        self.repro_tree.heading("ratio", text="ratio")
        self.repro_tree.heading("status", text="within band")
        self.repro_tree.column("#0", width=230, stretch=True)
        self.repro_tree.column("published", width=110, anchor="e")
        self.repro_tree.column("predicted", width=110, anchor="e")
        self.repro_tree.column("ratio", width=60, anchor="center")
        self.repro_tree.column("status", width=90, anchor="center")
        self.repro_tree.grid(row=0, column=0, sticky="ew")

        controls = ttk.Frame(repro_box)
        controls.grid(row=2, column=0, sticky="ew", padx=6, pady=(8, 4))
        ttk.Label(controls, text="Atoms (blank=paper default):").pack(side=LEFT)
        atoms_entry = ttk.Entry(controls, textvariable=self.repro_atoms_var, width=8)
        atoms_entry.pack(side=LEFT, padx=(4, 10))
        attach_tooltip(atoms_entry, "Override the ensemble size. Higher = lower projection-noise floor and a more faithful (but slower) reproduction. The regression suite uses 4000.")
        ttk.Label(controls, text="Drops:").pack(side=LEFT)
        drops_entry = ttk.Entry(controls, textvariable=self.repro_drops_var, width=8)
        drops_entry.pack(side=LEFT, padx=(4, 10))
        attach_tooltip(drops_entry, "Override the number of measurement drops. Blank uses the paper's default.")
        ttk.Button(controls, text="Load into editor →", command=lambda: self._load_selected_reproduction(run_after=False)).pack(side=LEFT, padx=4)
        ttk.Button(controls, text="Load & Run", style="Accent.TButton", command=lambda: self._load_selected_reproduction(run_after=True)).pack(side=LEFT, padx=4)

        qutip_box = ttk.Labelframe(right, text="Independent cross-check (QuTiP)", style="Section.TLabelframe")
        qutip_box.grid(row=2, column=0, sticky="nsew", pady=(6, 0))
        qutip_box.columnconfigure(0, weight=1)
        ttk.Label(
            qutip_box,
            text="qgrav computes each Raman pulse from a closed-form 2x2 matrix. These checks recompute the "
                 "same physics a different way and report the disagreement. 'AISim vs analytic' needs no extra "
                 "packages; the full QuTiP check integrates the Schrödinger equation independently.",
            wraplength=720,
            foreground="#5b6880",
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(2, 6))
        qbtns = ttk.Frame(qutip_box)
        qbtns.grid(row=1, column=0, sticky="ew", padx=6)
        self.btn_check_analytic = ttk.Button(qbtns, text="AISim vs analytic (no deps)", command=lambda: self._run_validation_check("analytic"))
        self.btn_check_analytic.pack(side=LEFT, padx=(0, 6))
        self.btn_check_qutip = ttk.Button(qbtns, text="Full QuTiP cross-check", command=lambda: self._run_validation_check("qutip"))
        self.btn_check_qutip.pack(side=LEFT, padx=6)
        ttk.Label(qbtns, textvariable=self.validation_status_var, foreground="#5b6880").pack(side=LEFT, padx=12)

        vr_frame = ttk.Frame(qutip_box)
        vr_frame.grid(row=2, column=0, sticky="nsew", padx=6, pady=(6, 6))
        qutip_box.rowconfigure(2, weight=1)
        vr_frame.rowconfigure(0, weight=1)
        vr_frame.columnconfigure(0, weight=1)
        self.validation_results = tk.Text(vr_frame, wrap="word", height=8)
        self.validation_results.grid(row=0, column=0, sticky="nsew")
        vr_scroll = ttk.Scrollbar(vr_frame, orient=VERTICAL, command=self.validation_results.yview)
        vr_scroll.grid(row=0, column=1, sticky="ns")
        self.validation_results.configure(yscrollcommand=vr_scroll.set)
        self.validation_results.insert(
            "1.0",
            "Pick a check above. Reproductions and cross-checks are independent:\n"
            " • reproductions test the full noise→g pipeline against published instruments;\n"
            " • cross-checks test the single-pulse quantum dynamics against an independent solver.\n",
        )

        self._populate_reference_library()
        self._populate_reproduction_tree()

    def _populate_reference_library(self) -> None:
        try:
            from qgrav.validation import REFERENCES
        except Exception as exc:  # pragma: no cover - defensive
            self.refs_tree.insert("", END, text=f"(could not load registry: {exc})")
            return
        self._references = REFERENCES
        for key in sorted(REFERENCES):
            ref = REFERENCES[key]
            self.refs_tree.insert(
                "", END, iid=key, text=key,
                values=(f"{ref.value:.3g}", ref.unit, ref.year),
            )

    def _on_reference_selected(self) -> None:
        sel = self.refs_tree.selection()
        if not sel:
            return
        ref = getattr(self, "_references", {}).get(sel[0])
        if ref is None:
            return
        lines = [
            f"{ref.key}",
            "",
            f"{ref.description}",
            "",
            f"Value      : {ref.value:.4g} {ref.unit}",
            f"Acceptance : ±{ref.tolerance_pct:.0f} %",
            f"Source     : {ref.source}",
            f"Year       : {ref.year}",
        ]
        if ref.doi:
            lines.append(f"DOI        : https://doi.org/{ref.doi}")
        self.ref_detail.configure(state="normal")
        self.ref_detail.delete("1.0", END)
        self.ref_detail.insert("1.0", "\n".join(lines))
        self.ref_detail.configure(state="disabled")

    def _reproduction_data(self) -> list[dict[str, Any]]:
        import importlib
        rows: list[dict[str, Any]] = []
        for suffix, label, role in self._REPRODUCTIONS:
            entry: dict[str, Any] = {"suffix": suffix, "label": label, "role": role}
            try:
                mod = importlib.import_module(f"qgrav.validation.{suffix}_setup")
                targets = next(v for k, v in vars(mod).items() if k.endswith("_TARGETS"))
                published = float(targets["short_term_noise_m_s2_per_sqrt_hz"])
                tol = float(targets.get("tolerance_factor", 2.0))
                predicted = float(mod.predicted_short_term_asd_m_s2_per_sqrt_hz())
                ratio = predicted / published if published else float("nan")
                entry.update(
                    module=mod, published=published, predicted=predicted,
                    ratio=ratio, tol=tol, within=(1.0 / tol) <= ratio <= tol,
                )
            except Exception as exc:  # pragma: no cover - defensive
                entry["error"] = str(exc)
            rows.append(entry)
        return rows

    def _populate_reproduction_tree(self) -> None:
        self._repro_rows = self._reproduction_data()
        self.repro_tree.delete(*self.repro_tree.get_children())
        for row in self._repro_rows:
            if "error" in row:
                self.repro_tree.insert("", END, iid=row["suffix"], text=f"{row['label']} (unavailable)",
                                       values=("—", "—", "—", "—"))
                continue
            self.repro_tree.insert(
                "", END, iid=row["suffix"],
                text=f"{row['label']}  [{row['role']}]",
                values=(
                    f"{row['published']:.2e}",
                    f"{row['predicted']:.2e}",
                    f"{row['ratio']:.2f}×",
                    "yes" if row["within"] else "no",
                ),
            )

    def _build_reproduction_config(self, row: dict[str, Any]) -> dict[str, Any]:
        mod = row["module"]
        kw = dict(mod.multi_drop_kwargs())
        # Coerce any numpy scalars to plain Python types for clean YAML.
        kw = {k: (v.item() if isinstance(v, np.generic) else v) for k, v in kw.items()}
        if self.repro_atoms_var.get().strip():
            kw["n_atoms"] = self._parse_required_int(self.repro_atoms_var, "Atoms")
        if self.repro_drops_var.get().strip():
            kw["n_drops"] = self._parse_required_int(self.repro_drops_var, "Drops")
        sim = {"enabled": True, "backend": "aisim", "model": "multi_drop_cycle"}
        sim.update(kw)
        return {
            "output": {"runs_dir": "runs", "name": f"{row['suffix']}_reproduction"},
            "bench": {"type": "virtual"},
            "stats": {"metrics_backend": "auto", "allan_data_type": "freq", "psd_method": "welch"},
            "simulation": sim,
        }

    def _load_selected_reproduction(self, *, run_after: bool) -> None:
        sel = self.repro_tree.selection()
        if not sel:
            messagebox.showinfo("qgrav", "Select a paper row in the table first.")
            return
        row = next((r for r in getattr(self, "_repro_rows", []) if r["suffix"] == sel[0]), None)
        if row is None or "error" in row:
            messagebox.showerror("qgrav", "That reproduction setup is unavailable in this build.")
            return
        try:
            cfg = self._build_reproduction_config(row)
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        self.editor.delete("1.0", END)
        self.editor.insert("1.0", yaml.safe_dump(cfg, sort_keys=False))
        self.config_path_var.set("")
        self.sync_controls_from_dict(cfg)
        self.workflow_var.set("synthetic")
        self._append_experiment_log(f"Loaded {row['label']} reproduction config.")
        self._append_log(self.live_summary, f"Loaded {row['label']} reproduction config into the editor.")
        if run_after:
            self.notebook.select(0)
            self.run_async()
        else:
            self.notebook.select(2)
            self.validation_status_var.set(f"Loaded {row['label']}. Press 'Run Pipeline' (top right) to reproduce it.")

    def _set_validation_busy(self, busy: bool) -> None:
        self._validation_busy = busy
        state = "disabled" if busy else "normal"
        for attr in ("btn_check_analytic", "btn_check_qutip"):
            btn = getattr(self, attr, None)
            if btn is not None:
                btn.configure(state=state)

    def _run_validation_check(self, mode: str) -> None:
        if self._validation_busy:
            return
        self._set_validation_busy(True)
        self.validation_status_var.set("Running cross-check…")
        threading.Thread(target=self._validation_worker, args=(mode,), daemon=True).start()

    def _validation_worker(self, mode: str) -> None:
        try:
            from qgrav.validation import qutip_crosscheck as qc

            omega = 2 * np.pi * np.array([5e3, 1e4, 2e4])
            deltas = 2 * np.pi * np.array([0.0, 2e3, -5e3])
            taus = np.array([10e-6, 23e-6, 50e-6])
            n_points = omega.size * deltas.size * taus.size
            if mode == "analytic":
                max_aa = 0.0
                for w in omega:
                    for d in deltas:
                        for t in taus:
                            p_ai = qc.aisim_rabi_population(float(w), float(d), float(t))
                            p_an = qc.analytic_rabi_population(float(w), float(d), float(t))
                            max_aa = max(max_aa, abs(p_ai - p_an))
                verdict = "PASS" if max_aa < 1e-9 else "CHECK"
                msg = (
                    "AISim closed-form matrix  vs  analytic Rabi formula\n"
                    f"  grid points              : {n_points}\n"
                    f"  max |P_aisim - P_analytic|: {max_aa:.2e}\n"
                    f"  verdict                  : {verdict}  (expected ~1e-15; no extra packages needed)\n"
                )
            else:
                res = qc.compare_rabi_grid(omega, deltas, taus)
                verdict = "PASS" if res["aisim_vs_qutip"] < 1e-4 else "CHECK"
                msg = (
                    "Independent QuTiP Schrödinger-integration cross-check\n"
                    f"  grid points            : {n_points}\n"
                    f"  max |AISim - QuTiP|    : {res['aisim_vs_qutip']:.2e}\n"
                    f"  max |AISim - analytic| : {res['aisim_vs_analytic']:.2e}\n"
                    f"  max |QuTiP - analytic| : {res['qutip_vs_analytic']:.2e}\n"
                    f"  verdict                : {verdict}  (an independent integrator agreeing validates the matrix)\n"
                )
            self._queue.put(("validation", msg))
        except ImportError:
            self._queue.put((
                "validation",
                "QuTiP is not installed.\n"
                "  Install it with:   pip install qgrav[qutip]\n"
                "  The 'AISim vs analytic' check needs no extra packages and works now.\n",
            ))
        except Exception as exc:  # pragma: no cover - defensive
            self._queue.put(("validation", f"Cross-check failed: {exc}\n"))

    def _build_guides_tab(self, parent: ttk.Frame) -> None:
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)
        pane = ttk.Panedwindow(parent, orient="horizontal")
        pane.grid(row=0, column=0, sticky="nsew")
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=1)
        pane.add(right, weight=3)
        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        nav_frame = ttk.Frame(left)
        nav_frame.grid(row=0, column=0, sticky="nsew")
        nav_frame.rowconfigure(0, weight=1)
        nav_frame.columnconfigure(0, weight=1)
        self.guide_nav = ttk.Treeview(nav_frame, show="tree", selectmode="browse")
        self.guide_nav.grid(row=0, column=0, sticky="nsew")
        nav_scroll = ttk.Scrollbar(nav_frame, orient=VERTICAL, command=self.guide_nav.yview)
        nav_scroll.grid(row=0, column=1, sticky="ns")
        self.guide_nav.configure(yscrollcommand=nav_scroll.set)
        self.guide_nav.bind("<<TreeviewSelect>>", lambda _e: self._on_guide_selected())

        toolbar = ttk.Frame(right)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        ttk.Label(toolbar, text="Guides & tips", foreground="#5b6880").pack(side=LEFT, padx=(2, 0))
        self.guide_open_btn = ttk.Button(toolbar, text="Open this document externally", command=self._open_current_guide_doc, state="disabled")
        self.guide_open_btn.pack(side="right")

        text_frame = ttk.Frame(right)
        text_frame.grid(row=1, column=0, sticky="nsew")
        text_frame.rowconfigure(0, weight=1)
        text_frame.columnconfigure(0, weight=1)
        self.guide_text = tk.Text(text_frame, wrap="word", padx=10, pady=8)
        self.guide_text.grid(row=0, column=0, sticky="nsew")
        guide_scroll = ttk.Scrollbar(text_frame, orient=VERTICAL, command=self.guide_text.yview)
        guide_scroll.grid(row=0, column=1, sticky="ns")
        self.guide_text.configure(yscrollcommand=guide_scroll.set, state="disabled")

        # node iid -> ("text", body) or ("file", Path)
        self._guide_entries: dict[str, tuple[str, Any]] = {}
        self._current_guide_path: Path | None = None

        topics_node = self.guide_nav.insert("", END, text="Guides & tips", open=True)
        for title, body in self._authored_guides().items():
            iid = self.guide_nav.insert(topics_node, END, text=title)
            self._guide_entries[iid] = ("text", body)

        docs = [
            ("Full user guide (GUIDE.md)", "GUIDE.md"),
            ("Complete guide", "docs/COMPLETE_GUIDE.md"),
            ("v1 physics upgrade", "docs/V1_PHYSICS_UPGRADE.md"),
            ("AISim gravimeter studies", "docs/AISIM_GRAVIMETER_STUDIES.md"),
            ("Scientific-package evaluation", "docs/SCIENTIFIC_PACKAGE_EVALUATION.md"),
            ("Physics review packet", "docs/PHYSICS_REVIEW_PACKET.md"),
            ("Performance notes", "docs/PERFORMANCE.md"),
            ("Roadmap v1 → v2", "docs/ROADMAP_V1_TO_V2.md"),
            ("Changelog", "CHANGELOG.md"),
        ]
        existing = [(label, rel) for label, rel in docs if (self._asset_root / rel).exists()]
        if existing:
            docs_node = self.guide_nav.insert("", END, text="Project documents", open=True)
            for label, rel in existing:
                iid = self.guide_nav.insert(docs_node, END, text=label)
                self._guide_entries[iid] = ("file", self._asset_root / rel)

        # Select the first authored topic by default.
        first = self.guide_nav.get_children(topics_node)
        if first:
            self.guide_nav.selection_set(first[0])
            self.guide_nav.focus(first[0])

    def _authored_guides(self) -> dict[str, str]:
        return {
            "Quick start": (
                "QUICK START — your first run in 4 steps\n"
                "=======================================\n\n"
                "1. Top toolbar -> Examples -> 'AISim Multi-drop (realistic ASD)'.\n"
                "   This loads a realistic repeated-drop gravimeter config.\n\n"
                "2. Press 'Run Pipeline' (top-right).\n\n"
                "3. Open the 'Results & Visuals' tab. Inspect the metric cards, the\n"
                "   metrics tree, and switch the plot selector between single plots\n"
                "   (gravity_series, PSD, Allan) before using the dashboard.\n\n"
                "4. Click 'Open HTML' to read the generated report.\n\n"
                "To reproduce a published instrument instead, go to the 'Validation'\n"
                "tab, pick a paper (e.g. Freier 2016), and press 'Load & Run'.\n"
            ),
            "Workflows": (
                "WORKFLOWS — pick the right one in Setup\n"
                "======================================\n\n"
                "real_data  : analyse measured gravity data (IGETS / Larzac / CSV /\n"
                "             .ggp). Produces PSD, Allan deviation, coverage checks,\n"
                "             and a report. Use the Data Browser to find a station.\n\n"
                "synthetic  : run the AISim atom-interferometer engine (Rabi, fringe,\n"
                "             gravity sweep, multi-drop cycle, vibration sweep).\n\n"
                "advanced   : edit YAML directly in the Config Editor for full control.\n\n"
                "The Setup form hides controls that don't apply to your workflow.\n"
            ),
            "Study models": (
                "STUDY MODELS — what each one computes\n"
                "=====================================\n\n"
                "rabi_scan               : excited fraction vs pulse duration. Use it\n"
                "                          to calibrate the pi/2 and pi pulse areas.\n\n"
                "mach_zehnder_phase_scan : one 3-pulse (pi/2 - pi - pi/2) fringe vs an\n"
                "                          applied laser phase. The basic interferometer.\n\n"
                "gravity_sweep           : fringe phase vs gravity g. With 'Gravity\n"
                "                          propagation' on, the phase EMERGES from real\n"
                "                          ballistic free-fall + a chirped laser rather\n"
                "                          than being injected analytically.\n\n"
                "multi_drop_cycle        : the flagship. Many repeated drops with a\n"
                "                          per-shot noise budget and a fringe-lock servo,\n"
                "                          producing a gravity time series -> ASD and\n"
                "                          Allan deviation, exactly like a real gravimeter.\n\n"
                "vibration_sensitivity_sweep : contrast / phase vs reference-mirror\n"
                "                          vibration amplitude.\n\n"
                "TIP: hover any control in Setup to see what it does.\n"
            ),
            "Noise & realism (multi-drop)": (
                "NOISE & REALISM — the multi-drop noise budget\n"
                "=============================================\n\n"
                "These knobs live in Setup under 'Multi-drop noise budget & servo'\n"
                "(collapsed by default) and only affect the multi_drop_cycle model.\n\n"
                "Detection sigma_p     : per-shot technical noise on the excited\n"
                "                        fraction. Blank = atom-shot-noise only.\n"
                "Raman phase noise     : per-shot laser + residual-vibration phase\n"
                "                        noise (rad RMS).\n"
                "Correlated vibration  : inject a time-correlated seismic series\n"
                "                        (Peterson NLNM/NHNM) instead of white noise.\n"
                "Isolation cutoff      : vibration-isolation corner frequency.\n"
                "Fit visibility        : fit the fringe contrast and use the same V\n"
                "                        for the P->g inversion (keeps the simulated\n"
                "                        ASD self-consistent with the injected budget).\n"
                "Servo                 : close a fringe-lock loop (integrator or full\n"
                "                        PID) as a real instrument does.\n\n"
                "IMPORTANT: the short-term sensitivity is set by the NOISE BUDGET, not\n"
                "the atom number. But too few atoms raises the projection-noise FLOOR\n"
                "(sigma_g ~ 1/sqrt(N)) and can swamp the budget. For a faithful\n"
                "reproduction use several thousand atoms.\n"
            ),
            "Validation & reproducing a paper": (
                "VALIDATION — reproduce a published instrument\n"
                "=============================================\n\n"
                "Open the 'Validation' tab.\n\n"
                "Left  : the registry of published reference values the automated\n"
                "        regression suite checks against. Click a row for source + DOI.\n\n"
                "Right : one-click reproductions. Each row builds a multi_drop_cycle\n"
                "        config from that paper's documented parameters + noise budget.\n"
                "        'Published' is the paper's reported short-term ASD; 'Predicted'\n"
                "        is qgrav's analytic value; 'ratio'/'within band' show agreement.\n\n"
                "        Select a paper, optionally raise 'Atoms' for fidelity, then\n"
                "        'Load & Run'. Freier 2016 is the primary regression target.\n\n"
                "HONESTY NOTE: these reproduce PUBLISHED numbers, not raw laboratory\n"
                "data, and have not yet had an independent expert physics review. See\n"
                "'How to move ahead' for how to change that.\n"
            ),
            "Interpreting results": (
                "INTERPRETING RESULTS\n"
                "====================\n\n"
                "PSD            : how noise power is distributed across frequency.\n"
                "                 A flat region is white noise; a 1/f slope is drift.\n"
                "Allan deviation: stability vs averaging time tau. A -1/2 (white) slope\n"
                "                 that keeps falling means averaging still helps; an\n"
                "                 upturn means drift/systematics dominate at long tau.\n"
                "ASD            : amplitude spectral density = sqrt(PSD); the usual way\n"
                "                 to quote a gravimeter's short-term sensitivity in\n"
                "                 m/s^2/sqrt(Hz).\n\n"
                "Every run also writes metrics.json, SUMMARY.md and an HTML report in\n"
                "its run folder (buttons on Setup and Results open them).\n"
            ),
            "Independent cross-checks": (
                "INDEPENDENT CROSS-CHECKS (QuTiP)\n"
                "================================\n\n"
                "On the Validation tab, the 'Independent cross-check' panel recomputes\n"
                "the single Raman-pulse quantum dynamics a different way and reports the\n"
                "disagreement with qgrav's closed-form 2x2 matrix.\n\n"
                "AISim vs analytic : compares the matrix to the textbook Rabi formula.\n"
                "                    Needs no extra packages; expect ~1e-15.\n"
                "Full QuTiP check  : integrates the Schrodinger equation with QuTiP, a\n"
                "                    genuinely independent solver. Expect ~1e-6. Install\n"
                "                    with  pip install qgrav[qutip]  if it is missing.\n\n"
                "An independent integrator agreeing is strong evidence the core\n"
                "atom-optics is correct (it does NOT validate the noise budget or the\n"
                "systematics — that is what the published-reference reproductions and a\n"
                "human review are for).\n"
            ),
            "How to move ahead": (
                "HOW TO MOVE AHEAD\n"
                "=================\n\n"
                "Inside qgrav (you can do these now):\n"
                "  1. Reproduce Freier 2016 on the Validation tab with Atoms = 4000.\n"
                "  2. Explore the noise budget: toggle correlated vibration and the\n"
                "     servo and watch the Allan deviation change.\n"
                "  3. Analyse real SG data: Data Browser -> 'Use sample' -> preview ->\n"
                "     'Use in Setup' -> Run. (Bundled IGETS sample, no download.)\n\n"
                "To make the project credible & citable (these are YOURS to do):\n"
                "  A. Independent physics review. Send docs/PHYSICS_REVIEW_PACKET.md to\n"
                "     an atom-interferometry group. This is the single highest-value\n"
                "     step — it is the one claim you cannot self-certify. It upgrades\n"
                "     the 'FULLY_SIMULATED' label from code-verified to peer-reviewed.\n"
                "  B. Publish the repo on GitHub and tag a release. This starts the\n"
                "     6-month public-history clock that JOSS requires.\n"
                "  C. Configure PyPI Trusted Publishing so users can pip install qgrav.\n"
                "  D. Submit paper/paper.md to JOSS for a citable DOI.\n"
                "  E. (Optional) Ask the groups you contact for anonymised raw\n"
                "     atom-gravimeter data — the one thing that would move validation\n"
                "     from 'published numbers' to 'real hardware'.\n\n"
                "Deferred engineering (documented in the roadmap, not blocking):\n"
                "  - sub-pulse integration to remove the residual calibration;\n"
                "  - BEC / non-thermal sources; 4- and 5-pulse interferometers;\n"
                "  - a hardware bench backend (v2.0).\n\n"
                "See 'Project documents -> Roadmap v1 -> v2' for the full plan.\n"
            ),
            "Glossary": (
                "GLOSSARY\n"
                "========\n\n"
                "Mach-Zehnder (MZ) : the 3-pulse pi/2 - pi - pi/2 atom interferometer.\n"
                "k_eff             : effective two-photon wavevector of the Raman pair.\n"
                "T                 : pulse-separation time. Phase ~ k_eff * g * T^2.\n"
                "Chirp             : laser frequency ramp that compensates the falling\n"
                "                    atoms' Doppler shift; its rate encodes g.\n"
                "Fringe / contrast : the cos(phi) interference signal and its amplitude.\n"
                "Projection noise  : fundamental 1/sqrt(N) detection limit.\n"
                "ASD / PSD         : amplitude / power spectral density.\n"
                "Allan deviation   : stability metric vs averaging time.\n"
                "IGETS             : International Geodynamics & Earth Tide Service\n"
                "                    (superconducting-gravimeter data archive).\n"
                "FULLY_SIMULATED   : computed from the microscopic propagator with no\n"
                "                    closed-form inertial-phase formula imposed.\n"
            ),
            "Common mistakes": (
                "COMMON MISTAKES\n"
                "===============\n\n"
                "- Reproducing a paper with too few atoms: the projection-noise floor\n"
                "  then dominates and the ASD looks too high. Raise Atoms to ~4000.\n"
                "- Reading the dashboard before the single plots: check gravity_series,\n"
                "  PSD and Allan individually first.\n"
                "- Editing the YAML and forgetting to press Run (the editor is the\n"
                "  source of truth for a run; 'Apply controls to editor' pushes the\n"
                "  Setup form into it).\n"
                "- Expecting multi_drop noise knobs to affect a rabi_scan or a fringe\n"
                "  scan — they only apply to multi_drop_cycle.\n"
                "- Running a real_data workflow with an empty station code or source.\n"
            ),
        }

    def _on_guide_selected(self) -> None:
        sel = self.guide_nav.selection()
        if not sel:
            return
        entry = self._guide_entries.get(sel[0])
        self._current_guide_path = None
        if entry is None:
            # A group header was clicked; expand/collapse, show nothing.
            return
        kind, payload = entry
        if kind == "text":
            body = str(payload)
        else:
            self._current_guide_path = payload
            try:
                body = payload.read_text(encoding="utf-8")
            except Exception as exc:
                body = f"(could not read {payload}: {exc})"
        self.guide_open_btn.configure(state=("normal" if self._current_guide_path else "disabled"))
        self.guide_text.configure(state="normal")
        self.guide_text.delete("1.0", END)
        self.guide_text.insert("1.0", body)
        self.guide_text.configure(state="disabled")
        self.guide_text.yview_moveto(0.0)

    def _open_current_guide_doc(self) -> None:
        if self._current_guide_path and self._current_guide_path.exists():
            webbrowser.open(self._current_guide_path.resolve().as_uri())

    def _labeled_entry(self, parent: ttk.Frame, label: str, variable: tk.StringVar, row: int, column: int, tip: str = "") -> None:
        box = ttk.Frame(parent)
        box.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        lbl = ttk.Label(box, text=label)
        lbl.pack(anchor="w")
        entry = ttk.Entry(box, textvariable=variable)
        entry.pack(fill=X)
        if tip:
            attach_tooltip(lbl, tip)
            attach_tooltip(entry, tip)

    def _labeled_combo(self, parent: ttk.Frame, label: str, variable: tk.StringVar, values: list[str], row: int, column: int, tip: str = "") -> None:
        box = ttk.Frame(parent)
        box.grid(row=row, column=column, sticky="ew", padx=6, pady=6)
        lbl = ttk.Label(box, text=label)
        lbl.pack(anchor="w")
        combo = ttk.Combobox(box, textvariable=variable, values=values, state="readonly")
        combo.pack(fill=X)
        if tip:
            attach_tooltip(lbl, tip)
            attach_tooltip(combo, tip)

    def _labeled_check(self, parent: ttk.Frame, label: str, variable: tk.BooleanVar, row: int, column: int, tip: str = "") -> None:
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

    def _bind_variable_traces(self) -> None:
        self.workflow_var.trace_add("write", lambda *_: self._on_workflow_changed())
        self.bench_type_var.trace_add("write", lambda *_: self._sync_workflow_sections())
        self.sim_enabled_var.trace_add("write", lambda *_: self._sync_workflow_sections())
        self.sim_model_var.trace_add("write", lambda *_: self._sync_workflow_sections())

    def _workflow_from_config(self, cfg: dict[str, Any]) -> str:
        simulation = cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
        bench_type = str(cfg.get("bench", {}).get("type", "virtual"))
        if bool(simulation.get("enabled", False)):
            return "synthetic"
        if bench_type in {"real", "real_gravity"}:
            return "real_data"
        return "advanced"

    def _on_workflow_changed(self) -> None:
        workflow = self.workflow_var.get().strip() or "real_data"
        if workflow == "real_data":
            if self.bench_type_var.get() not in {"real", "real_gravity"}:
                self.bench_type_var.set("real_gravity")
            self.sim_enabled_var.set(False)
        elif workflow == "synthetic":
            self.bench_type_var.set("virtual")
            self.sim_enabled_var.set(True)
        self._sync_workflow_sections()

    @staticmethod
    def _show_frame(widget: ttk.Widget, visible: bool) -> None:
        if visible:
            if not widget.winfo_manager():
                widget.pack(fill=X, expand=False, pady=(0, 10))
        else:
            if widget.winfo_manager():
                widget.pack_forget()

    def _sync_workflow_sections(self) -> None:
        workflow = self.workflow_var.get().strip() or "real_data"
        bench_type = self.bench_type_var.get().strip() or "virtual"
        show_real = workflow == "real_data"
        show_synth = workflow == "synthetic" or bool(self.sim_enabled_var.get())

        self._show_frame(self.real_data_frame, show_real)
        self._show_frame(self.synthetic_frame, show_synth)
        self._show_frame(self.workflow_compare_note, workflow == "advanced")

        if show_real:
            self.workflow_summary_var.set("Analyze real gravimetry data from IGETS, Larzac, CSV, or .ggp sources.")
            self.next_steps_var.set("1. Choose a dataset source.  2. Select a station.  3. Preview data quality.  4. Run the benchmark.")
            self.current_context_var.set("Recommended for PSD, Allan deviation, coverage/gap checks, and report generation.")
        elif show_synth:
            self.workflow_summary_var.set("Run a synthetic atom-gravimeter study with AISim-backed or hybrid gravimeter models.")
            self.next_steps_var.set("1. Choose a study model.  2. Keep defaults for a first run.  3. Run simulation.  4. Inspect truth checks and report.")
            self.current_context_var.set("Recommended for phase scan, gravity sweep, and vibration sensitivity studies.")
        else:
            self.workflow_summary_var.set("Advanced mode exposes all controls for manual editing and configuration work.")
            self.next_steps_var.set("Use Load/Validate, edit YAML as needed, then run the pipeline. Results and comparisons appear in the Results tab.")
            self.current_context_var.set("Use this mode only if you already understand the config structure.")

        if bench_type == "real":
            self._show_frame(self.real_ifo_subframe, True)
            self._show_frame(self.real_gravity_subframe, False)
        else:
            self._show_frame(self.real_ifo_subframe, False)
            self._show_frame(self.real_gravity_subframe, show_real)

    def _set_running_state(self, is_running: bool) -> None:
        self._run_in_progress = is_running
        self.run_button.configure(state=("disabled" if is_running else "normal"))

    def _parse_required_float(self, variable: tk.StringVar, label: str) -> float:
        raw = variable.get().strip()
        if not raw:
            raise ValueError(f"{label} is required.")
        try:
            return float(raw)
        except ValueError as exc:
            raise ValueError(f"{label} must be a valid number.") from exc

    def _parse_required_int(self, variable: tk.StringVar, label: str) -> int:
        return int(self._parse_required_float(variable, label))

    def _parse_zernike(self) -> list[float] | None:
        raw = self.sim_wavefront_zernike_var.get().strip()
        if not raw:
            return None
        tokens = [t for t in raw.replace(";", ",").split(",") if t.strip()]
        try:
            return [float(t) for t in tokens]
        except ValueError as exc:
            raise ValueError(
                "Wavefront Zernike coeffs must be a comma-separated list of numbers "
                "(metres of wavefront error), e.g. '0, 0, 0, 5e-9'."
            ) from exc

    def _apply_advanced_physics(self, sim: dict[str, Any], *, with_propagation: bool, with_lock: bool) -> None:
        """Write the optional 'Advanced physics' knobs into a simulation dict."""
        if self.sim_single_photon_detuning_var.get().strip():
            sim["single_photon_detuning_hz"] = self._parse_required_float(
                self.sim_single_photon_detuning_var, "Single-photon detuning (Hz)"
            )
        zern = self._parse_zernike()
        if zern is not None:
            sim["wavefront_zernike_coeffs"] = zern
            sim["wavefront_radius_m"] = self._parse_required_float(
                self.sim_wavefront_radius_var, "Wavefront radius (m)"
            )
        if with_propagation:
            sim["gravity_propagation"] = bool(self.sim_gravity_propagation_var.get())
            if self.sim_gravity_gradient_var.get().strip():
                sim["gravity_gradient_per_m"] = self._parse_required_float(
                    self.sim_gravity_gradient_var, "Gravity gradient (1/m)"
                )
        if with_lock:
            sim["lock_to_midfringe"] = bool(self.sim_lock_to_midfringe_var.get())

    def _apply_multi_drop_noise(self, sim: dict[str, Any]) -> None:
        """Write the multi-drop noise-budget + servo knobs into a simulation dict."""
        sim["n_drops"] = self._parse_required_int(self.sim_n_drops_var, "Drops per cycle")
        sim["cycle_time_s"] = self._parse_required_float(self.sim_cycle_time_var, "Cycle time (s)")
        sim["gravity_true_m_s2"] = self._parse_required_float(self.sim_gravity_true_var, "True gravity (m/s²)")
        if self.sim_detection_sigma_p_var.get().strip():
            sim["detection_sigma_p"] = self._parse_required_float(
                self.sim_detection_sigma_p_var, "Detection sigma_p"
            )
        if self.sim_raman_phase_noise_var.get().strip():
            sim["raman_phase_noise_rad"] = self._parse_required_float(
                self.sim_raman_phase_noise_var, "Raman phase noise (rad)"
            )
        if bool(self.sim_correlated_vibration_var.get()):
            sim["correlated_vibration"] = True
            sim["seismic_model"] = self.sim_seismic_model_var.get().strip() or "nlnm"
            if self.sim_isolation_cutoff_var.get().strip():
                sim["vibration_isolation_cutoff_hz"] = self._parse_required_float(
                    self.sim_isolation_cutoff_var, "Isolation cutoff (Hz)"
                )
        if bool(self.sim_fit_visibility_var.get()):
            sim["fit_visibility"] = True
        if bool(self.sim_servo_enabled_var.get()):
            sim["servo_enabled"] = True
            sim["servo_type"] = self.sim_servo_type_var.get().strip() or "integrator"
            sim["servo_kp"] = self._parse_required_float(self.sim_servo_kp_var, "Servo kp")
            sim["servo_ki"] = self._parse_required_float(self.sim_servo_ki_var, "Servo ki")
            sim["servo_kd"] = self._parse_required_float(self.sim_servo_kd_var, "Servo kd")

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
                if hasattr(p, 'exists') and p.exists():
                    p.unlink()
                elif isinstance(p, str):
                    if os.path.exists(p):
                        os.unlink(p)
            except Exception:
                pass
        self._temp_config_paths.clear()

    def pick_config(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*")])
        if path:
            self.config_path_var.set(path)
            self.load_config_into_editor(Path(path))

    def load_current_path(self) -> None:
        path_text = self.config_path_var.get().strip()
        if not path_text:
            messagebox.showerror("qgrav", "Choose a config file first.")
            return
        self.load_config_into_editor(Path(path_text))

    def load_config_into_editor(self, path: Path) -> None:
        try:
            cfg, text = load_config(path)
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        # Remember the real project root so temp configs resolve relative paths correctly
        self._project_root = find_project_root(path)
        self.editor.delete("1.0", END)
        self.editor.insert("1.0", text)
        self.sync_controls_from_dict(cfg)
        self._append_log(self.live_summary, f"Loaded config: {path}")
        self._append_experiment_log(f"Loaded config: {path}")

    def _load_bundled_example(self) -> None:
        path = self._asset_root / "configs" / "example.yaml"
        if path.exists():
            self.config_path_var.set(str(path))
            self.load_config_into_editor(path)

    def _load_bundled_aisim_example(self) -> None:
        path = self._asset_root / "configs" / "example_aisim.yaml"
        if path.exists():
            self.config_path_var.set(str(path))
            self.load_config_into_editor(path)

    def _load_bundled_aisim_phase_example(self) -> None:
        path = self._asset_root / "configs" / "example_aisim_phase_scan.yaml"
        if not path.exists():
            messagebox.showerror("qgrav", f"Bundled config missing: {path}")
            return
        self.config_path_var.set(str(path))
        self.load_config_into_editor(path)

    def _load_bundled_aisim_gravity_example(self) -> None:
        path = self._asset_root / "configs" / "example_aisim_gravity_sweep.yaml"
        if not path.exists():
            messagebox.showerror("qgrav", f"Bundled config missing: {path}")
            return
        self.config_path_var.set(str(path))
        self.load_config_into_editor(path)

    def _load_bundled_aisim_vibration_example(self) -> None:
        path = self._asset_root / "configs" / "example_aisim_vibration_sweep.yaml"
        if not path.exists():
            messagebox.showerror("qgrav", f"Bundled config missing: {path}")
            return
        self.config_path_var.set(str(path))
        self.load_config_into_editor(path)

    def _load_bundled_aisim_multi_drop_example(self) -> None:
        path = self._asset_root / "configs" / "example_aisim_multi_drop.yaml"
        if not path.exists():
            messagebox.showerror("qgrav", f"Bundled config missing: {path}")
            return
        self.config_path_var.set(str(path))
        self.load_config_into_editor(path)

    def _load_bundled_real_gravity_example(self) -> None:
        path = self._asset_root / "configs" / "example_real_gravity.yaml"
        if path.exists():
            self.config_path_var.set(str(path))
            self.load_config_into_editor(path)
            self.browser_dataset_var.set(str(self._asset_root / "data" / "raw" / "sg_sample"))

    def save_editor_as(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".yaml", filetypes=[("YAML files", "*.yaml *.yml")])
        if path:
            Path(path).write_text(self.editor.get("1.0", END), encoding="utf-8")
            self.config_path_var.set(path)
            self.status_var.set(f"Saved config to {path}")

    def _materialize_editor_to_path(self, editor_text: str) -> Path:
        path_text = self.config_path_var.get().strip()
        if path_text:
            path = Path(path_text)
            try:
                existing = path.read_text(encoding="utf-8") if path.exists() else None
            except Exception:
                existing = None
            if existing == editor_text:
                return path
        return self._materialize_editor_to_temp_path(editor_text)

    def _editor_config(self) -> dict[str, Any]:
        cfg = yaml.safe_load(self.editor.get("1.0", END))
        if not isinstance(cfg, dict):
            raise ValueError(
                "Configuration root must be a YAML mapping (dictionary).\n\n"
                "The editor may be empty or contain invalid YAML.\n"
                "Load a config file or choose one from the Examples menu."
            )
        return cfg

    def validate_editor_config(self) -> None:
        try:
            cfg = self._editor_config()
            issues = validate_config_structure(cfg)
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        if issues:
            msg = "Validation issues found:\n- " + "\n- ".join(issues)
            messagebox.showwarning("qgrav", msg)
            self._append_log(self.live_summary, msg)
            self._append_experiment_log(msg)
        else:
            messagebox.showinfo("qgrav", "Configuration looks valid.")
            self._append_log(self.live_summary, "Validation passed with no structural issues.")
            self._append_experiment_log("Validation passed with no structural issues.")

    def sync_controls_from_dict(self, cfg: dict[str, Any]) -> None:
        self.run_name_var.set(str(cfg.get("output", {}).get("name", "example")))
        self.bench_type_var.set(str(cfg.get("bench", {}).get("type", "virtual")))
        self.workflow_var.set(self._workflow_from_config(cfg))
        stats = cfg.get("stats", {}) if isinstance(cfg.get("stats", {}), dict) else {}
        self.backend_var.set(str(stats.get("metrics_backend", stats.get("allan_backend", "auto"))))
        self.data_type_var.set(str(stats.get("allan_data_type", "freq")))
        self.psd_method_var.set(str(stats.get("psd_method", "welch")))
        self.compare_backends_var.set(bool(stats.get("compare_allan_backends", False)))

        virtual = cfg.get("bench_virtual_ifo", {}) if isinstance(cfg.get("bench_virtual_ifo", {}), dict) else {}
        self.sample_rate_var.set(str(virtual.get("sample_rate_hz", "")))
        self.duration_var.set(str(virtual.get("duration_s", "")))
        real_ifo = cfg.get("bench_real_ifo", {}) if isinstance(cfg.get("bench_real_ifo", {}), dict) else {}
        self.real_ifo_path_var.set(str(real_ifo.get("csv_path", "")))
        real_gravity = cfg.get("bench_real_gravity", {}) if isinstance(cfg.get("bench_real_gravity", {}), dict) else {}
        self.real_gravity_source_var.set(str(real_gravity.get("source_path", "")))
        self.real_gravity_station_var.set(str(real_gravity.get("station_code", "")))

        simulation = cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
        sim_model = str(simulation.get("model", "rabi_scan"))
        self.sim_enabled_var.set(bool(simulation.get("enabled", False)))
        self.sim_backend_var.set(str(simulation.get("backend", "aisim")))
        self.sim_model_var.set(sim_model)
        self.sim_atoms_var.set(str(simulation.get("n_atoms", "500")))
        self.sim_tau_step_var.set(str(simulation.get("tau_step_s", "1e-6")))
        self.sim_tau_pi_half_var.set(str(simulation.get("tau_pi_half_s", "2.3e-5")))
        self.sim_interferometer_time_var.set(str(simulation.get("interferometer_time_s", "0.260")))
        self.sim_gravity_center_var.set(str(simulation.get("gravity_center_m_s2", simulation.get("gravity_ref_m_s2", "9.81"))))
        self.sim_gravity_span_var.set(str(simulation.get("gravity_span_m_s2", "6e-6")))
        self.sim_vibration_freq_var.set(str(simulation.get("vibration_frequency_hz", "1.0")))
        self.sim_vibration_amp_max_var.set(str(simulation.get("amplitude_max_m", "5e-8")))

        # Advanced physics knobs
        self.sim_seed_var.set(str(simulation.get("seed", "1")))
        self.sim_single_photon_detuning_var.set(str(simulation.get("single_photon_detuning_hz", "0.0")))
        self.sim_gravity_propagation_var.set(bool(simulation.get("gravity_propagation", False)))
        self.sim_lock_to_midfringe_var.set(bool(simulation.get("lock_to_midfringe", True)))
        self.sim_gravity_gradient_var.set(str(simulation.get("gravity_gradient_per_m", "0.0")))
        zernike = simulation.get("wavefront_zernike_coeffs")
        if isinstance(zernike, (list, tuple)):
            self.sim_wavefront_zernike_var.set(", ".join(str(c) for c in zernike))
        else:
            self.sim_wavefront_zernike_var.set(str(zernike) if zernike else "")
        self.sim_wavefront_radius_var.set(str(simulation.get("wavefront_radius_m", "0.05")))

        # Multi-drop realism knobs
        self.sim_n_drops_var.set(str(simulation.get("n_drops", "100")))
        self.sim_cycle_time_var.set(str(simulation.get("cycle_time_s", "1.0")))
        self.sim_gravity_true_var.set(str(simulation.get("gravity_true_m_s2", "9.81")))
        sigma_p = simulation.get("detection_sigma_p")
        self.sim_detection_sigma_p_var.set("" if sigma_p is None else str(sigma_p))
        self.sim_raman_phase_noise_var.set(str(simulation.get("raman_phase_noise_rad", "0.0")))
        self.sim_correlated_vibration_var.set(bool(simulation.get("correlated_vibration", False)))
        self.sim_seismic_model_var.set(str(simulation.get("seismic_model", "nlnm")))
        self.sim_isolation_cutoff_var.set(str(simulation.get("vibration_isolation_cutoff_hz", "0.0")))
        self.sim_fit_visibility_var.set(bool(simulation.get("fit_visibility", False)))
        self.sim_servo_enabled_var.set(bool(simulation.get("servo_enabled", False)))
        self.sim_servo_type_var.set(str(simulation.get("servo_type", "integrator")))
        self.sim_servo_kp_var.set(str(simulation.get("servo_kp", "0.5")))
        self.sim_servo_ki_var.set(str(simulation.get("servo_ki", "0.1")))
        self.sim_servo_kd_var.set(str(simulation.get("servo_kd", "0.0")))

        if sim_model == "rabi_scan":
            self.sim_steps_var.set(str(simulation.get("n_steps", "50")))
        elif sim_model == "mach_zehnder_phase_scan":
            self.sim_steps_var.set(str(simulation.get("n_phase_points", "50")))
        elif sim_model == "gravity_sweep":
            self.sim_steps_var.set(str(simulation.get("n_gravity_points", "50")))
        elif sim_model == "vibration_sensitivity_sweep":
            self.sim_steps_var.set(str(simulation.get("n_amplitude_points", "50")))
        else:
            self.sim_steps_var.set(str(simulation.get("n_steps", "50")))
        self._sync_workflow_sections()

    def sync_controls_from_editor(self) -> None:
        try:
            cfg = self._editor_config()
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        self.sync_controls_from_dict(cfg)
        self._append_log(self.live_summary, "Quick controls refreshed from editor.")
        self._append_experiment_log("Quick controls refreshed from editor.")

    def apply_quick_controls_to_editor(self) -> None:
        try:
            cfg = self._editor_config()
            workflow = self.workflow_var.get().strip() or "real_data"
            bench_type = self.bench_type_var.get().strip() or "virtual"
            if workflow == "real_data" and bench_type not in {"real", "real_gravity"}:
                bench_type = "real_gravity"
            elif workflow == "synthetic":
                bench_type = "virtual"
                self.sim_enabled_var.set(True)

            cfg.setdefault("output", {})["name"] = self.run_name_var.get().strip() or "example"
            cfg.setdefault("bench", {})["type"] = bench_type
            stats = cfg.setdefault("stats", {})
            stats["metrics_backend"] = self.backend_var.get().strip() or "auto"
            stats["allan_data_type"] = self.data_type_var.get().strip() or "freq"
            stats["psd_method"] = self.psd_method_var.get().strip() or "welch"
            stats["compare_allan_backends"] = bool(self.compare_backends_var.get())

            if bench_type == "virtual":
                virt = cfg.setdefault("bench_virtual_ifo", {})
                if self.sample_rate_var.get().strip():
                    virt["sample_rate_hz"] = self._parse_required_float(self.sample_rate_var, "Sample rate (Hz)")
                if self.duration_var.get().strip():
                    virt["duration_s"] = self._parse_required_float(self.duration_var, "Duration (s)")
            elif bench_type == "real":
                real_ifo = cfg.setdefault("bench_real_ifo", {})
                csv_path = self.real_ifo_path_var.get().strip()
                if not csv_path:
                    raise ValueError("Real IFO CSV is required for bench type 'real'.")
                real_ifo["csv_path"] = csv_path
                if self.sample_rate_var.get().strip():
                    real_ifo["sample_rate_hz"] = self._parse_required_float(self.sample_rate_var, "Sample rate (Hz)")
            elif bench_type == "real_gravity":
                grav = cfg.setdefault("bench_real_gravity", {})
                source_path = self.real_gravity_source_var.get().strip()
                if not source_path:
                    raise ValueError("Gravity source is required for bench type 'real_gravity'.")
                grav["source_path"] = source_path
                if self.real_gravity_station_var.get().strip():
                    grav["station_code"] = self.real_gravity_station_var.get().strip()
                grav.setdefault("segment_strategy", "longest_contiguous")

            sim = cfg.setdefault("simulation", {})
            sim_enabled = bool(self.sim_enabled_var.get())
            sim["enabled"] = sim_enabled
            sim["backend"] = self.sim_backend_var.get().strip() or "aisim"
            sim_model = self.sim_model_var.get().strip() or "rabi_scan"
            sim["model"] = sim_model
            if sim_enabled:
                sim["n_atoms"] = self._parse_required_int(self.sim_atoms_var, "Atoms")
                sim["tau_pi_half_s"] = self._parse_required_float(self.sim_tau_pi_half_var, "π/2 pulse duration (s)")
                if self.sim_seed_var.get().strip():
                    sim["seed"] = self._parse_required_int(self.sim_seed_var, "Random seed")
                if sim_model == "rabi_scan":
                    sim["n_steps"] = self._parse_required_int(self.sim_steps_var, "Steps / points")
                    sim["tau_step_s"] = self._parse_required_float(self.sim_tau_step_var, "Tau step (s)")
                elif sim_model == "mach_zehnder_phase_scan":
                    sim["n_phase_points"] = self._parse_required_int(self.sim_steps_var, "Steps / points")
                    sim["interferometer_time_s"] = self._parse_required_float(self.sim_interferometer_time_var, "Interferometer T (s)")
                    self._apply_advanced_physics(sim, with_propagation=False, with_lock=False)
                elif sim_model == "gravity_sweep":
                    sim["n_gravity_points"] = self._parse_required_int(self.sim_steps_var, "Steps / points")
                    sim["interferometer_time_s"] = self._parse_required_float(self.sim_interferometer_time_var, "Interferometer T (s)")
                    sim["gravity_center_m_s2"] = self._parse_required_float(self.sim_gravity_center_var, "Gravity center (m/s²)")
                    sim["gravity_span_m_s2"] = self._parse_required_float(self.sim_gravity_span_var, "Gravity span (m/s²)")
                    self._apply_advanced_physics(sim, with_propagation=True, with_lock=True)
                elif sim_model == "multi_drop_cycle":
                    sim["interferometer_time_s"] = self._parse_required_float(self.sim_interferometer_time_var, "Interferometer T (s)")
                    self._apply_advanced_physics(sim, with_propagation=True, with_lock=False)
                    self._apply_multi_drop_noise(sim)
                elif sim_model == "vibration_sensitivity_sweep":
                    sim["n_amplitude_points"] = self._parse_required_int(self.sim_steps_var, "Steps / points")
                    sim["interferometer_time_s"] = self._parse_required_float(self.sim_interferometer_time_var, "Interferometer T (s)")
                    sim["gravity_ref_m_s2"] = self._parse_required_float(self.sim_gravity_center_var, "Gravity center (m/s²)")
                    sim["vibration_frequency_hz"] = self._parse_required_float(self.sim_vibration_freq_var, "Vibration freq (Hz)")
                    sim["amplitude_max_m"] = self._parse_required_float(self.sim_vibration_amp_max_var, "Max vibration amp (m)")

            self.editor.delete("1.0", END)
            self.editor.insert("1.0", yaml.safe_dump(cfg, sort_keys=False))
            self._append_log(self.live_summary, "Applied quick controls back into YAML editor.")
            self._append_experiment_log("Applied quick controls back into YAML editor.")
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            self._append_log(self.live_summary, f"Quick-control apply failed: {exc}")
            self._append_experiment_log(f"Quick-control apply failed: {exc}")

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
                preferred = "gravity_series" if "gravity_series" in kinds else ("displacement" if "displacement" in kinds else kinds[0])
                self.plot_kind_var.set(preferred)
                self.current_context_var.set("Run complete. Open the report or inspect single plots first (gravity_series / displacement / PSD) before switching to dashboard.")
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

    def _populate_metrics_tree(self, metrics: dict[str, Any]) -> None:
        self.metrics_tree.delete(*self.metrics_tree.get_children())

        def add_items(parent: str, prefix: str, value: Any) -> None:
            if isinstance(value, dict):
                node = self.metrics_tree.insert(parent, END, text=prefix, values=("",))
                for key, sub in value.items():
                    add_items(node, str(key), sub)
            elif isinstance(value, list):
                node = self.metrics_tree.insert(parent, END, text=prefix, values=("",))
                for idx, sub in enumerate(value):
                    add_items(node, f"[{idx}]", sub)
            else:
                self.metrics_tree.insert(parent, END, text=prefix, values=(str(value),))

        for key, value in metrics.items():
            add_items("", str(key), value)

    def _render_figure(self, fig: Figure, *, canvas_attr: str, toolbar_attr: str, frame: ttk.Frame, toolbar_frame: ttk.Frame | None = None) -> None:
        current_canvas = getattr(self, canvas_attr, None)
        if current_canvas is not None:
            old_figure = current_canvas.figure
            current_canvas.get_tk_widget().destroy()
            plt.close(old_figure)
        current_toolbar = getattr(self, toolbar_attr, None)
        if current_toolbar is not None:
            current_toolbar.destroy()
        host_toolbar = toolbar_frame if toolbar_frame is not None else frame
        canvas = FigureCanvasTkAgg(fig, master=frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        toolbar = NavigationToolbar2Tk(canvas, host_toolbar, pack_toolbar=False)
        toolbar.update()
        toolbar.grid(row=0, column=0, sticky="w")
        setattr(self, canvas_attr, canvas)
        setattr(self, toolbar_attr, toolbar)

    def refresh_plot(self) -> None:
        if not self.last_bundle:
            return
        plot_name = self.plot_kind_var.get().strip() or "dashboard"
        fig = build_run_figure(self.last_bundle, plot_name)
        descriptions = {
            "gravity_series": "Use this first for real-data runs to understand drift, events, and coverage over time.",
            "psd": "Use PSD to inspect frequency-domain noise structure.",
            "allan": "Use Allan deviation to study stability versus averaging time.",
            "dashboard": "Dashboard combines several summaries, but single plots are usually easier to interpret first.",
            "displacement": "Use this first for synthetic interferometer runs.",
        }
        self.plot_title_var.set(f"{plot_name}: {descriptions.get(plot_name, 'Interactive plot view.')}")
        self._render_figure(fig, canvas_attr="_current_canvas", toolbar_attr="_current_toolbar", frame=self.plot_frame, toolbar_frame=self.plot_toolbar_frame)

    def _browse_dataset_source(self) -> None:
        choice = messagebox.askyesnocancel(
            "Select dataset source",
            "Choose Yes to browse for a file/archive, No to browse for a directory, or Cancel to abort.",
        )
        if choice is None:
            return
        if choice:
            path = filedialog.askopenfilename(title="Select dataset archive or station file")
        else:
            path = filedialog.askdirectory(title="Select gravimetry dataset directory")
        if path:
            self.browser_dataset_var.set(path)

    def _load_sample_dataset(self) -> None:
        path = self._asset_root / "data" / "raw" / "sg_sample"
        self.browser_dataset_var.set(str(path))
        self.scan_dataset_source()

    def scan_dataset_source(self) -> None:
        source = self.browser_dataset_var.get().strip()
        if not source:
            messagebox.showerror("qgrav", "Choose a dataset source first.")
            return
        try:
            stations = list_stations_in_source(source)
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        self.station_tree.delete(*self.station_tree.get_children())
        for item in stations:
            self.station_tree.insert("", END, text=item["station_code"], values=(item.get("longitude_deg"), item.get("latitude_deg")))
        self.station_info.delete("1.0", END)
        self.station_info.insert("1.0", f"Loaded {len(stations)} stations from {source}\nSelect a station to preview.\n")

    def _on_station_selected(self) -> None:
        selected = self.station_tree.selection()
        if not selected:
            return
        item = self.station_tree.item(selected[0])
        code = str(item["text"])
        self.browser_station_var.set(code)
        self.station_info.delete("1.0", END)
        self.station_info.insert("1.0", f"Station: {code}\nLongitude: {item['values'][0]}\nLatitude: {item['values'][1]}\n")

    def _build_station_preview_figure(self, data: dict[str, Any]) -> Figure:
        fig = Figure(figsize=(9.6, 6.4), dpi=110, constrained_layout=True)
        axes = fig.subplots(2, 2)
        for ax in axes.flat:
            ax.tick_params(labelsize=8)
        t_full = np.asarray(data["t_full"], dtype=np.float64)
        x_full = np.asarray(data["gravity_residual_full"], dtype=np.float64)
        t = np.asarray(data["t"], dtype=np.float64)
        x = np.asarray(data["gravity_residual"], dtype=np.float64)
        fs = float(data["sample_rate_hz"])
        span = t[-1] - t[0] if len(t) > 1 else 1.0
        taus = np.logspace(np.log10(1.0 / fs), np.log10(max(2.0 / fs, 0.25 * span)), 20)
        adev = allan_deviation_overlapping(x, fs, taus, backend="auto", data_type="freq")
        psd = compute_psd(x, fs, method="welch", nperseg=min(max(8, len(x) // 4), len(x)), noverlap=max(1, min(len(x) // 8, len(x) // 4 - 1)))

        ax = axes[0, 0]
        ax.plot(t_full / 86400.0, x_full, linewidth=0.8)
        ax.set_title("Gravity series")
        ax.set_xlabel("days from start")

        ax = axes[0, 1]
        ax.hist(x, bins=40, alpha=0.85)
        ax.set_title("Histogram")

        ax = axes[1, 0]
        ax.loglog(psd["f_hz"][1:], psd["psd"][1:])
        ax.set_title("PSD")
        ax.set_xlabel("frequency (Hz)")

        ax = axes[1, 1]
        ax.loglog(np.asarray(adev["taus_s"]), np.asarray(adev["adev"]))
        ax.set_title("Allan deviation")
        ax.set_xlabel("tau (s)")
        return fig

    def preview_selected_station(self) -> None:
        source = self.browser_dataset_var.get().strip()
        station = self.browser_station_var.get().strip()
        if not source or not station:
            messagebox.showerror("qgrav", "Select a dataset source and a station first.")
            return
        try:
            data = load_real_gravity(source_path=source, station_code=station, segment_strategy="longest_contiguous")
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        self._browser_data = data
        fig = self._build_station_preview_figure(data)
        self._render_figure(fig, canvas_attr="_browser_canvas", toolbar_attr="_browser_toolbar", frame=self.browser_plot_frame, toolbar_frame=self.browser_toolbar_frame)
        info = data.get("gap_report", {})
        segment = data.get("analysis_segment", {})
        self.station_info.delete("1.0", END)
        self.station_info.insert(
            "1.0",
            f"Station: {data.get('station_code')}\n"
            f"Start: {data.get('record_start')}\n"
            f"End: {data.get('record_end')}\n"
            f"Median dt (s): {info.get('median_dt_s')}\n"
            f"Gap count: {info.get('gap_count')}\n"
            f"Missing samples estimate: {info.get('missing_samples_estimate')}\n"
            f"Analysis segment samples: {segment.get('segment_samples')}\n",
        )

    def create_real_gravity_config_from_selection(self) -> None:
        source = self.browser_dataset_var.get().strip()
        station = self.browser_station_var.get().strip()
        if not source or not station:
            messagebox.showerror("qgrav", "Select a dataset source and a station first.")
            return
        cfg = {
            "output": {"runs_dir": "runs", "name": f"gravity_{station}"},
            "bench": {"type": "real_gravity"},
            "bench_real_gravity": {"source_path": source, "station_code": station, "segment_strategy": "longest_contiguous"},
            "stats": {
                "metrics_backend": self.backend_var.get().strip() or "auto",
                "allan_data_type": "freq",
                "psd_method": self.psd_method_var.get().strip() or "welch",
                "welch_nperseg": 256,
                "welch_noverlap": 128,
                "compare_allan_backends": bool(self.compare_backends_var.get()),
                "comparison_backend": "custom",
            },
            "simulation": {"enabled": False},
        }
        self.editor.delete("1.0", END)
        self.editor.insert("1.0", yaml.safe_dump(cfg, sort_keys=False))
        self.bench_type_var.set("real_gravity")
        self.real_gravity_source_var.set(source)
        self.real_gravity_station_var.set(station)
        self.workflow_var.set("real_data")
        self._append_log(self.live_summary, f"Created real_gravity config for station {station}.")
        self._append_experiment_log(f"Created real_gravity config for station {station}.")

    def _use_browser_selection_for_gravity(self) -> None:
        source = self.browser_dataset_var.get().strip()
        station = self.browser_station_var.get().strip()
        if not source:
            messagebox.showinfo("qgrav", "Scan or choose a dataset source in Data Browser first.")
            return
        self.workflow_var.set("real_data")
        self.bench_type_var.set("real_gravity")
        self.real_gravity_source_var.set(source)
        if station:
            self.real_gravity_station_var.set(station)
        self.current_context_var.set("Data Browser selection copied into Setup. Apply controls to editor or run directly.")

    def open_report(self) -> None:
        if self.last_report:
            webbrowser.open(self.last_report.resolve().as_uri())
        else:
            messagebox.showinfo("qgrav", "Run the pipeline first.")

    def open_run_folder(self) -> None:
        if self.last_report:
            webbrowser.open(self.last_report.parent.resolve().as_uri())
        else:
            messagebox.showinfo("qgrav", "Run the pipeline first.")

    def open_metrics_file(self) -> None:
        if self.last_report:
            webbrowser.open((self.last_report.parent / "metrics.json").resolve().as_uri())
        else:
            messagebox.showinfo("qgrav", "Run the pipeline first.")

    def open_summary_file(self) -> None:
        if self.last_report:
            webbrowser.open((self.last_report.parent / "SUMMARY.md").resolve().as_uri())
        else:
            messagebox.showinfo("qgrav", "Run the pipeline first.")


def main(default_config: Path | None = None) -> None:
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        raise RuntimeError("GUI could not start. This environment may be headless or missing Tk support.") from exc
    app = QGravApp(root, default_config=default_config)
    root.protocol("WM_DELETE_WINDOW", lambda: (app._cleanup_temp_configs(), root.destroy()))
    root.mainloop()
