"""Setup & Run tab: workflow picker, quick controls, advanced physics +
multi-drop noise sections, bundled examples, run-config assembly.

Moved verbatim out of ``app.py`` (v1.4 modularisation).
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import BOTH, LEFT, VERTICAL, X, messagebox, ttk
from typing import Any

from qgrav.gui.widgets import CollapsibleSection, ScrollableFrame, attach_tooltip
from qgrav.metrics import available_allan_backends

logger = logging.getLogger(__name__)


class SetupRunTabMixin:
    """Setup & Run tab: workflow picker, quick controls, advanced physics +
    multi-drop noise sections, bundled examples, run-config assembly.

        Mixed into :class:`qgrav.gui.app.QGravApp`, which owns every shared
        ``self`` attribute (Tk variables, ``_queue``, ``_project_root``, ...)
        created in ``QGravApp.__init__``. Worker threads must communicate
        only via ``self._queue.put(...)`` - never touch Tk widgets directly
        from a thread (the Tk thread polls the queue via ``_poll_queue``).
    """

    def _build_examples_menu(self, parent: ttk.Frame) -> ttk.Menubutton:
        menu_btn = ttk.Menubutton(parent, text="Examples")
        menu = tk.Menu(menu_btn, tearoff=False)
        menu.add_command(label="Default example", command=self._load_bundled_example)
        menu.add_separator()
        menu.add_command(label="AISim Rabi", command=self._load_bundled_aisim_example)
        menu.add_command(label="AISim Phase", command=self._load_bundled_aisim_phase_example)
        menu.add_command(label="AISim Gravity", command=self._load_bundled_aisim_gravity_example)
        menu.add_command(
            label="AISim Multi-drop (realistic ASD)",
            command=self._load_bundled_aisim_multi_drop_example,
        )
        menu.add_command(
            label="AISim Vibration", command=self._load_bundled_aisim_vibration_example
        )
        menu.add_separator()
        menu.add_command(
            label="Real gravity example", command=self._load_bundled_real_gravity_example
        )
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

        self.workflow_frame = ttk.Labelframe(
            controls_parent, text="Start Here", style="Section.TLabelframe"
        )
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
        ttk.Label(
            self.workflow_frame,
            textvariable=self.workflow_summary_var,
            wraplength=430,
            foreground="#334e68",
        ).pack(anchor="w", padx=6, pady=(8, 2))
        ttk.Label(
            self.workflow_frame,
            textvariable=self.next_steps_var,
            wraplength=430,
            foreground="#5b6880",
        ).pack(anchor="w", padx=6, pady=(0, 2))

        self.analysis_frame = ttk.Labelframe(
            controls_parent, text="Analysis settings", style="Section.TLabelframe"
        )
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
        self._labeled_combo(
            analysis_fields,
            "Allan backend",
            self.backend_var,
            ["auto", "custom"] + [b for b in available_allan_backends() if b not in {"custom"}],
            0,
            1,
        )
        self._labeled_combo(
            analysis_fields, "Allan data type", self.data_type_var, ["freq", "phase"], 1, 0
        )
        self._labeled_combo(
            analysis_fields, "PSD method", self.psd_method_var, ["welch", "periodogram"], 1, 1
        )
        ttk.Checkbutton(
            analysis_fields, text="Compare Allan backends", variable=self.compare_backends_var
        ).grid(row=2, column=0, sticky="w", padx=6, pady=6)
        ttk.Label(
            analysis_fields,
            text="Use Allantools/Welch for report-quality real-data analysis. Periodogram/custom are mainly for debugging or comparison.",
            wraplength=430,
            foreground="#5b6880",
        ).grid(row=2, column=1, sticky="w", padx=6, pady=6)

        self.real_data_frame = ttk.Labelframe(
            controls_parent, text="Real-data input", style="Section.TLabelframe"
        )
        self.real_data_frame.pack(fill=X, expand=False, pady=(0, 10))
        real_top = ttk.Frame(self.real_data_frame)
        real_top.pack(fill=X, expand=True)
        for col in range(2):
            real_top.columnconfigure(col, weight=1)
        self._labeled_combo(
            real_top, "Bench type", self.bench_type_var, ["real_gravity", "real"], 0, 0
        )
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
        self._labeled_entry(
            rg_fields, "Gravity source (.zip/.ggp/dir/csv)", self.real_gravity_source_var, 0, 0
        )
        self._labeled_entry(rg_fields, "Gravity station code", self.real_gravity_station_var, 0, 1)
        ttk.Button(
            self.real_gravity_subframe,
            text="Use browser selection",
            command=self._use_browser_selection_for_gravity,
        ).pack(anchor="w", padx=6, pady=(4, 0))

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

        self.synthetic_frame = ttk.Labelframe(
            controls_parent, text="Synthetic gravimeter study", style="Section.TLabelframe"
        )
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
        attach_tooltip(
            en,
            "Turn the synthetic atom-interferometer engine on. When off, the pipeline only does data analysis.",
        )
        self._labeled_combo(
            sim_top,
            "Simulation backend",
            self.sim_backend_var,
            ["aisim"],
            0,
            1,
            tip="AISim is the vendored semiclassical atom-interferometer backend (the only backend currently shipped).",
        )
        self._labeled_combo(
            sim_top,
            "Study model",
            self.sim_model_var,
            [
                "rabi_scan",
                "mach_zehnder_phase_scan",
                "gravity_sweep",
                "multi_drop_cycle",
                "vibration_sensitivity_sweep",
            ],
            1,
            0,
            tip=(
                "rabi_scan: pulse-area calibration.\n"
                "mach_zehnder_phase_scan: a single 3-pulse fringe.\n"
                "gravity_sweep: fringe phase vs g (emergent-gravity check).\n"
                "multi_drop_cycle: realistic repeated drops with noise + servo -> ASD/Allan (the flagship model).\n"
                "vibration_sensitivity_sweep: contrast vs reference-mirror vibration."
            ),
        )
        self._labeled_entry(
            sim_top,
            "Atoms",
            self.sim_atoms_var,
            1,
            1,
            tip="Number of atoms in the Monte-Carlo ensemble. More atoms = lower projection-noise floor (sigma_g ~ 1/sqrt(N)) but slower.",
        )
        self._labeled_entry(
            sim_top,
            "Steps / points",
            self.sim_steps_var,
            2,
            0,
            tip="Number of scan points (Rabi tau steps, phase points, or gravity points). Ignored by multi_drop_cycle (use 'drops per cycle' below).",
        )
        self._labeled_entry(
            sim_top,
            "π/2 pulse duration (s)",
            self.sim_tau_pi_half_var,
            2,
            1,
            tip="Duration of a pi/2 Raman pulse. Freier 2016 uses ~17 us; the default is 23 us.",
        )
        self._labeled_entry(
            sim_top,
            "Tau step (s)",
            self.sim_tau_step_var,
            3,
            0,
            tip="Rabi-scan pulse-duration increment per step (rabi_scan only).",
        )
        self._labeled_entry(
            sim_top,
            "Interferometer T (s)",
            self.sim_interferometer_time_var,
            3,
            1,
            tip="Pulse-separation time T. Phase scales as k_eff*g*T^2, so sensitivity grows as T^2. Freier 2016 uses 260 ms.",
        )
        self._labeled_entry(
            sim_top,
            "Gravity center (m/s²)",
            self.sim_gravity_center_var,
            4,
            0,
            tip="Central gravity value for a gravity_sweep, or the reference g for vibration studies.",
        )
        self._labeled_entry(
            sim_top,
            "Gravity span (m/s²)",
            self.sim_gravity_span_var,
            4,
            1,
            tip="Full width of the gravity_sweep around the centre value (e.g. 6e-6 m/s^2).",
        )
        self._labeled_entry(
            sim_top,
            "Vibration freq (Hz)",
            self.sim_vibration_freq_var,
            5,
            0,
            tip="Reference-mirror vibration frequency (vibration_sensitivity_sweep only).",
        )
        self._labeled_entry(
            sim_top,
            "Max vibration amp (m)",
            self.sim_vibration_amp_max_var,
            5,
            1,
            tip="Largest mirror-vibration amplitude in the sweep (vibration_sensitivity_sweep only).",
        )

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
        self._labeled_entry(
            adv_fields,
            "Random seed",
            self.sim_seed_var,
            0,
            0,
            tip="Seed for the atom-ensemble RNG. Fix it for reproducible runs.",
        )
        self._labeled_entry(
            adv_fields,
            "Single-photon detuning (Hz)",
            self.sim_single_photon_detuning_var,
            0,
            1,
            tip="Raman single-photon detuning Delta. Sets the AC-Stark / light shift. Freier 2016 uses about -700 MHz.",
        )
        self._labeled_check(
            adv_fields,
            "Gravity propagation (ballistic)",
            self.sim_gravity_propagation_var,
            1,
            0,
            tip="If on, the phase emerges from real ballistic free-fall + chirped laser instead of being injected analytically. The honest 'emergent gravity' path.",
        )
        self._labeled_check(
            adv_fields,
            "Lock to mid-fringe",
            self.sim_lock_to_midfringe_var,
            1,
            1,
            tip="gravity_sweep only: bias the interferometer to the steepest, most sensitive point of the fringe.",
        )
        self._labeled_entry(
            adv_fields,
            "Gravity gradient (1/m)",
            self.sim_gravity_gradient_var,
            2,
            0,
            tip="Vertical gravity gradient d g / d z (e.g. -3.1e-6 s^-2). 0 disables it.",
        )
        self._labeled_entry(
            adv_fields,
            "Wavefront Zernike coeffs",
            self.sim_wavefront_zernike_var,
            2,
            1,
            tip="Comma-separated Zernike coefficients in metres of wavefront error, e.g. '0,0,0,5e-9' (defocus). Blank = flat wavefront.",
        )
        self._labeled_entry(
            adv_fields,
            "Wavefront radius (m)",
            self.sim_wavefront_radius_var,
            3,
            0,
            tip="Beam radius over which the Zernike wavefront is normalised (default 0.05 m).",
        )

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
        self._labeled_entry(
            nf,
            "Drops per cycle",
            self.sim_n_drops_var,
            0,
            0,
            tip="Number of repeated measurement drops. The simulated ASD/Allan curve is built from this time series.",
        )
        self._labeled_entry(
            nf,
            "Cycle time (s)",
            self.sim_cycle_time_var,
            0,
            1,
            tip="Time per drop (1/repetition-rate). Sets the time axis for ASD and Allan deviation. Freier 2016: 1.5 s.",
        )
        self._labeled_entry(
            nf,
            "True gravity (m/s²)",
            self.sim_gravity_true_var,
            1,
            0,
            tip="The ground-truth g the simulated instrument is trying to recover.",
        )
        self._labeled_entry(
            nf,
            "Detection sigma_p",
            self.sim_detection_sigma_p_var,
            1,
            1,
            tip="Per-shot detection noise on the excited fraction P (technical/electronic). Blank = use shot-noise from atom number only. Freier 2016: ~6e-3.",
        )
        self._labeled_entry(
            nf,
            "Raman phase noise (rad)",
            self.sim_raman_phase_noise_var,
            2,
            0,
            tip="Per-shot laser/Raman + residual-vibration phase noise (rad RMS), added directly to the interferometer phase.",
        )
        self._labeled_check(
            nf,
            "Correlated seismic vibration",
            self.sim_correlated_vibration_var,
            2,
            1,
            tip="If on, inject a time-correlated seismic vibration series (Peterson model) instead of white phase noise.",
        )
        self._labeled_combo(
            nf,
            "Seismic model",
            self.sim_seismic_model_var,
            ["nlnm", "nhnm"],
            3,
            0,
            tip="Peterson New Low / High Noise Model for the correlated seismic background.",
        )
        self._labeled_entry(
            nf,
            "Isolation cutoff (Hz)",
            self.sim_isolation_cutoff_var,
            3,
            1,
            tip="Vibration-isolation corner frequency. Vibration below this is suppressed. 0 = no isolation.",
        )
        self._labeled_check(
            nf,
            "Fit fringe visibility",
            self.sim_fit_visibility_var,
            4,
            0,
            tip="Fit the contrast V from the simulated data and use the same V for the P->g inversion (keeps the noise budget self-consistent).",
        )
        self._labeled_check(
            nf,
            "Emergent projection noise",
            self.sim_projection_noise_var,
            5,
            1,
            tip=(
                "Draw each drop's detected count from Binomial(N_det, P) so quantum "
                "projection noise emerges from single-atom statistics instead of a "
                "configured Gaussian. Technical sigma_p (if set) adds on top."
            ),
        )
        self._labeled_check(
            nf,
            "Enable fringe-lock servo",
            self.sim_servo_enabled_var,
            4,
            1,
            tip="Close a feedback loop that steers each drop back to mid-fringe (as a real gravimeter does).",
        )
        self._labeled_combo(
            nf,
            "Servo type",
            self.sim_servo_type_var,
            ["integrator", "pid"],
            5,
            0,
            tip="integrator: simple I servo. pid: full proportional-integral-derivative with anti-windup.",
        )
        servo_gains = ttk.Frame(nf)
        servo_gains.grid(row=6, column=0, columnspan=2, sticky="ew")
        for col in range(3):
            servo_gains.columnconfigure(col, weight=1)
        self._labeled_entry(
            servo_gains, "Servo kp", self.sim_servo_kp_var, 0, 0, tip="Proportional gain (pid)."
        )
        self._labeled_entry(
            servo_gains,
            "Servo ki",
            self.sim_servo_ki_var,
            0,
            1,
            tip="Integral gain (integrator and pid).",
        )
        self._labeled_entry(
            servo_gains, "Servo kd", self.sim_servo_kd_var, 0, 2, tip="Derivative gain (pid)."
        )

        self.workflow_compare_note = ttk.Labelframe(
            controls_parent, text="Advanced mode", style="Section.TLabelframe"
        )
        self.workflow_compare_note.pack(fill=X, expand=False, pady=(0, 10))
        ttk.Label(
            self.workflow_compare_note,
            text="Use this mode when you want to edit YAML directly or inspect previous runs. Compare plots and metrics from the Results tab after a run.",
            wraplength=430,
            foreground="#5b6880",
        ).pack(anchor="w", padx=6, pady=6)

        actions = ttk.Labelframe(controls_parent, text="Actions", style="Section.TLabelframe")
        actions.pack(fill=X, expand=False, pady=(0, 10))
        ttk.Label(
            actions, textvariable=self.current_context_var, wraplength=430, foreground="#5b6880"
        ).pack(anchor="w", padx=6, pady=(2, 6))
        btns = ttk.Frame(actions)
        btns.pack(fill=X, padx=6, pady=(0, 4))
        ttk.Button(btns, text="Pull from editor", command=self.sync_controls_from_editor).pack(
            side=LEFT, padx=(0, 6)
        )
        ttk.Button(
            btns, text="Apply controls to editor", command=self.apply_quick_controls_to_editor
        ).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="Open report", command=self.open_report).pack(side=LEFT, padx=6)
        ttk.Button(btns, text="Open run folder", command=self.open_run_folder).pack(
            side=LEFT, padx=6
        )

        summary = ttk.Labelframe(
            right, text="Recommended next steps & run summary", style="Section.TLabelframe"
        )
        summary.grid(row=0, column=0, sticky="nsew", pady=(0, 8))
        summary.rowconfigure(1, weight=1)
        summary.columnconfigure(0, weight=1)
        ttk.Label(
            summary, textvariable=self.next_steps_var, wraplength=760, foreground="#334e68"
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 8))
        summary_frame = ttk.Frame(summary)
        summary_frame.grid(row=1, column=0, sticky="nsew")
        summary_frame.rowconfigure(0, weight=1)
        summary_frame.columnconfigure(0, weight=1)
        self.live_summary = tk.Text(summary_frame, wrap="word", height=24)
        self.live_summary.grid(row=0, column=0, sticky="nsew")
        summary_scroll = ttk.Scrollbar(
            summary_frame, orient=VERTICAL, command=self.live_summary.yview
        )
        summary_scroll.grid(row=0, column=1, sticky="ns")
        self.live_summary.configure(yscrollcommand=summary_scroll.set)
        self.live_summary.insert(
            "1.0", "Load a config, choose a workflow, then run the pipeline.\n"
        )

        runlog = ttk.Labelframe(right, text="Live run log", style="Section.TLabelframe")
        runlog.grid(row=1, column=0, sticky="nsew")
        runlog.rowconfigure(0, weight=1)
        runlog.columnconfigure(0, weight=1)
        self.experiment_log = tk.Text(runlog, wrap="word", height=10)
        self.experiment_log.grid(row=0, column=0, sticky="nsew")
        runlog_scroll = ttk.Scrollbar(runlog, orient=VERTICAL, command=self.experiment_log.yview)
        runlog_scroll.grid(row=0, column=1, sticky="ns")
        self.experiment_log.configure(yscrollcommand=runlog_scroll.set)

    def _bind_variable_traces(self) -> None:
        self.workflow_var.trace_add("write", lambda *_: self._on_workflow_changed())
        self.bench_type_var.trace_add("write", lambda *_: self._sync_workflow_sections())
        self.sim_enabled_var.trace_add("write", lambda *_: self._sync_workflow_sections())
        self.sim_model_var.trace_add("write", lambda *_: self._sync_workflow_sections())

    def _workflow_from_config(self, cfg: dict[str, Any]) -> str:
        simulation = (
            cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
        )
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
            self.workflow_summary_var.set(
                "Analyze real gravimetry data from IGETS, Larzac, CSV, or .ggp sources."
            )
            self.next_steps_var.set(
                "1. Choose a dataset source.  2. Select a station.  3. Preview data quality.  4. Run the benchmark."
            )
            self.current_context_var.set(
                "Recommended for PSD, Allan deviation, coverage/gap checks, and report generation."
            )
        elif show_synth:
            self.workflow_summary_var.set(
                "Run a synthetic atom-gravimeter study with AISim-backed or hybrid gravimeter models."
            )
            self.next_steps_var.set(
                "1. Choose a study model.  2. Keep defaults for a first run.  3. Run simulation.  4. Inspect truth checks and report."
            )
            self.current_context_var.set(
                "Recommended for phase scan, gravity sweep, and vibration sensitivity studies."
            )
        else:
            self.workflow_summary_var.set(
                "Advanced mode exposes all controls for manual editing and configuration work."
            )
            self.next_steps_var.set(
                "Use Load/Validate, edit YAML as needed, then run the pipeline. Results and comparisons appear in the Results tab."
            )
            self.current_context_var.set(
                "Use this mode only if you already understand the config structure."
            )

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

    def _apply_advanced_physics(
        self, sim: dict[str, Any], *, with_propagation: bool, with_lock: bool
    ) -> None:
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
        sim["gravity_true_m_s2"] = self._parse_required_float(
            self.sim_gravity_true_var, "True gravity (m/s²)"
        )
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
        if bool(self.sim_projection_noise_var.get()):
            sim["projection_noise"] = True
        if bool(self.sim_servo_enabled_var.get()):
            sim["servo_enabled"] = True
            sim["servo_type"] = self.sim_servo_type_var.get().strip() or "integrator"
            sim["servo_kp"] = self._parse_required_float(self.sim_servo_kp_var, "Servo kp")
            sim["servo_ki"] = self._parse_required_float(self.sim_servo_ki_var, "Servo ki")
            sim["servo_kd"] = self._parse_required_float(self.sim_servo_kd_var, "Servo kd")

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
