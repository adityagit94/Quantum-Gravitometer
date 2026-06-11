"""Config Editor tab: YAML editor, load/save, validation, and the
quick-controls <-> editor sync (sync_controls_from_dict /
apply_quick_controls_to_editor).

Moved verbatim out of ``app.py`` (v1.4 modularisation).
"""

from __future__ import annotations

import logging
import tkinter as tk
from pathlib import Path
from tkinter import END, VERTICAL, filedialog, messagebox, ttk
from typing import Any

import yaml

from qgrav.config import find_project_root, load_config, validate_config_structure

logger = logging.getLogger(__name__)


class EditorTabMixin:
    """Config Editor tab: YAML editor, load/save, validation, and the
    quick-controls <-> editor sync (sync_controls_from_dict /
    apply_quick_controls_to_editor).

        Mixed into :class:`qgrav.gui.app.QGravApp`, which owns every shared
        ``self`` attribute (Tk variables, ``_queue``, ``_project_root``, ...)
        created in ``QGravApp.__init__``. Worker threads must communicate
        only via ``self._queue.put(...)`` - never touch Tk widgets directly
        from a thread (the Tk thread polls the queue via ``_poll_queue``).
    """

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

    def pick_config(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("YAML files", "*.yaml *.yml"), ("All files", "*")]
        )
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

    def save_editor_as(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".yaml", filetypes=[("YAML files", "*.yaml *.yml")]
        )
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

        virtual = (
            cfg.get("bench_virtual_ifo", {})
            if isinstance(cfg.get("bench_virtual_ifo", {}), dict)
            else {}
        )
        self.sample_rate_var.set(str(virtual.get("sample_rate_hz", "")))
        self.duration_var.set(str(virtual.get("duration_s", "")))
        real_ifo = (
            cfg.get("bench_real_ifo", {}) if isinstance(cfg.get("bench_real_ifo", {}), dict) else {}
        )
        self.real_ifo_path_var.set(str(real_ifo.get("csv_path", "")))
        real_gravity = (
            cfg.get("bench_real_gravity", {})
            if isinstance(cfg.get("bench_real_gravity", {}), dict)
            else {}
        )
        self.real_gravity_source_var.set(str(real_gravity.get("source_path", "")))
        self.real_gravity_station_var.set(str(real_gravity.get("station_code", "")))

        simulation = (
            cfg.get("simulation", {}) if isinstance(cfg.get("simulation", {}), dict) else {}
        )
        sim_model = str(simulation.get("model", "rabi_scan"))
        self.sim_enabled_var.set(bool(simulation.get("enabled", False)))
        self.sim_backend_var.set(str(simulation.get("backend", "aisim")))
        self.sim_model_var.set(sim_model)
        self.sim_atoms_var.set(str(simulation.get("n_atoms", "500")))
        self.sim_tau_step_var.set(str(simulation.get("tau_step_s", "1e-6")))
        self.sim_tau_pi_half_var.set(str(simulation.get("tau_pi_half_s", "2.3e-5")))
        self.sim_interferometer_time_var.set(str(simulation.get("interferometer_time_s", "0.260")))
        self.sim_gravity_center_var.set(
            str(simulation.get("gravity_center_m_s2", simulation.get("gravity_ref_m_s2", "9.81")))
        )
        self.sim_gravity_span_var.set(str(simulation.get("gravity_span_m_s2", "6e-6")))
        self.sim_vibration_freq_var.set(str(simulation.get("vibration_frequency_hz", "1.0")))
        self.sim_vibration_amp_max_var.set(str(simulation.get("amplitude_max_m", "5e-8")))

        # Advanced physics knobs
        self.sim_seed_var.set(str(simulation.get("seed", "1")))
        self.sim_single_photon_detuning_var.set(
            str(simulation.get("single_photon_detuning_hz", "0.0"))
        )
        self.sim_gravity_propagation_var.set(bool(simulation.get("gravity_propagation", False)))
        self.sim_lock_to_midfringe_var.set(bool(simulation.get("lock_to_midfringe", True)))
        self.sim_gravity_gradient_var.set(str(simulation.get("gravity_gradient_per_m", "0.0")))
        zernike = simulation.get("wavefront_zernike_coeffs")
        if isinstance(zernike, list | tuple):
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
        self.sim_isolation_cutoff_var.set(
            str(simulation.get("vibration_isolation_cutoff_hz", "0.0"))
        )
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
                    virt["sample_rate_hz"] = self._parse_required_float(
                        self.sample_rate_var, "Sample rate (Hz)"
                    )
                if self.duration_var.get().strip():
                    virt["duration_s"] = self._parse_required_float(
                        self.duration_var, "Duration (s)"
                    )
            elif bench_type == "real":
                real_ifo = cfg.setdefault("bench_real_ifo", {})
                csv_path = self.real_ifo_path_var.get().strip()
                if not csv_path:
                    raise ValueError("Real IFO CSV is required for bench type 'real'.")
                real_ifo["csv_path"] = csv_path
                if self.sample_rate_var.get().strip():
                    real_ifo["sample_rate_hz"] = self._parse_required_float(
                        self.sample_rate_var, "Sample rate (Hz)"
                    )
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
                sim["tau_pi_half_s"] = self._parse_required_float(
                    self.sim_tau_pi_half_var, "π/2 pulse duration (s)"
                )
                if self.sim_seed_var.get().strip():
                    sim["seed"] = self._parse_required_int(self.sim_seed_var, "Random seed")
                if sim_model == "rabi_scan":
                    sim["n_steps"] = self._parse_required_int(self.sim_steps_var, "Steps / points")
                    sim["tau_step_s"] = self._parse_required_float(
                        self.sim_tau_step_var, "Tau step (s)"
                    )
                elif sim_model == "mach_zehnder_phase_scan":
                    sim["n_phase_points"] = self._parse_required_int(
                        self.sim_steps_var, "Steps / points"
                    )
                    sim["interferometer_time_s"] = self._parse_required_float(
                        self.sim_interferometer_time_var, "Interferometer T (s)"
                    )
                    self._apply_advanced_physics(sim, with_propagation=False, with_lock=False)
                elif sim_model == "gravity_sweep":
                    sim["n_gravity_points"] = self._parse_required_int(
                        self.sim_steps_var, "Steps / points"
                    )
                    sim["interferometer_time_s"] = self._parse_required_float(
                        self.sim_interferometer_time_var, "Interferometer T (s)"
                    )
                    sim["gravity_center_m_s2"] = self._parse_required_float(
                        self.sim_gravity_center_var, "Gravity center (m/s²)"
                    )
                    sim["gravity_span_m_s2"] = self._parse_required_float(
                        self.sim_gravity_span_var, "Gravity span (m/s²)"
                    )
                    self._apply_advanced_physics(sim, with_propagation=True, with_lock=True)
                elif sim_model == "multi_drop_cycle":
                    sim["interferometer_time_s"] = self._parse_required_float(
                        self.sim_interferometer_time_var, "Interferometer T (s)"
                    )
                    self._apply_advanced_physics(sim, with_propagation=True, with_lock=False)
                    self._apply_multi_drop_noise(sim)
                elif sim_model == "vibration_sensitivity_sweep":
                    sim["n_amplitude_points"] = self._parse_required_int(
                        self.sim_steps_var, "Steps / points"
                    )
                    sim["interferometer_time_s"] = self._parse_required_float(
                        self.sim_interferometer_time_var, "Interferometer T (s)"
                    )
                    sim["gravity_ref_m_s2"] = self._parse_required_float(
                        self.sim_gravity_center_var, "Gravity center (m/s²)"
                    )
                    sim["vibration_frequency_hz"] = self._parse_required_float(
                        self.sim_vibration_freq_var, "Vibration freq (Hz)"
                    )
                    sim["amplitude_max_m"] = self._parse_required_float(
                        self.sim_vibration_amp_max_var, "Max vibration amp (m)"
                    )

            self.editor.delete("1.0", END)
            self.editor.insert("1.0", yaml.safe_dump(cfg, sort_keys=False))
            self._append_log(self.live_summary, "Applied quick controls back into YAML editor.")
            self._append_experiment_log("Applied quick controls back into YAML editor.")
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            self._append_log(self.live_summary, f"Quick-control apply failed: {exc}")
            self._append_experiment_log(f"Quick-control apply failed: {exc}")
