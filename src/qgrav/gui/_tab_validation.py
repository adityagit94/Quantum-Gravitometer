"""Validation tab: published-reference library, one-click
reproductions, and the QuTiP/AISim cross-check worker.

Moved verbatim out of ``app.py`` (v1.4 modularisation).
"""

from __future__ import annotations

import logging
import threading
import tkinter as tk
from tkinter import END, LEFT, VERTICAL, messagebox, ttk
from typing import Any

import numpy as np
import yaml

from qgrav.gui.widgets import attach_tooltip

logger = logging.getLogger(__name__)


class ValidationTabMixin:
    """Validation tab: published-reference library, one-click
    reproductions, and the QuTiP/AISim cross-check worker.

        Mixed into :class:`qgrav.gui.app.QGravApp`, which owns every shared
        ``self`` attribute (Tk variables, ``_queue``, ``_project_root``, ...)
        created in ``QGravApp.__init__``. Worker threads must communicate
        only via ``self._queue.put(...)`` - never touch Tk widgets directly
        from a thread (the Tk thread polls the queue via ``_poll_queue``).
    """

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

        refs_box = ttk.Labelframe(
            left, text="Published reference library", style="Section.TLabelframe"
        )
        refs_box.grid(row=1, column=0, sticky="nsew")
        refs_box.rowconfigure(0, weight=1)
        refs_box.columnconfigure(0, weight=1)
        self.refs_tree = ttk.Treeview(
            refs_box, columns=("value", "unit", "year"), show="tree headings", height=12
        )
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

        ttk.Label(left, text="Reference details", foreground="#5b6880").grid(
            row=2, column=0, sticky="w", padx=4, pady=(8, 0)
        )
        detail_frame = ttk.Frame(left)
        detail_frame.grid(row=3, column=0, sticky="nsew")
        detail_frame.rowconfigure(0, weight=1)
        detail_frame.columnconfigure(0, weight=1)
        self.ref_detail = tk.Text(detail_frame, wrap="word", height=7)
        self.ref_detail.grid(row=0, column=0, sticky="nsew")
        ref_detail_scroll = ttk.Scrollbar(
            detail_frame, orient=VERTICAL, command=self.ref_detail.yview
        )
        ref_detail_scroll.grid(row=0, column=1, sticky="ns")
        self.ref_detail.configure(yscrollcommand=ref_detail_scroll.set, state="disabled")

        # --- RIGHT: reproductions + QuTiP cross-check --------------------
        repro_box = ttk.Labelframe(
            right, text="Reproduce a published measurement (one click)", style="Section.TLabelframe"
        )
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
        attach_tooltip(
            atoms_entry,
            "Override the ensemble size. Higher = lower projection-noise floor and a more faithful (but slower) reproduction. The regression suite uses 4000.",
        )
        ttk.Label(controls, text="Drops:").pack(side=LEFT)
        drops_entry = ttk.Entry(controls, textvariable=self.repro_drops_var, width=8)
        drops_entry.pack(side=LEFT, padx=(4, 10))
        attach_tooltip(
            drops_entry, "Override the number of measurement drops. Blank uses the paper's default."
        )
        ttk.Button(
            controls,
            text="Load into editor →",
            command=lambda: self._load_selected_reproduction(run_after=False),
        ).pack(side=LEFT, padx=4)
        ttk.Button(
            controls,
            text="Load & Run",
            style="Accent.TButton",
            command=lambda: self._load_selected_reproduction(run_after=True),
        ).pack(side=LEFT, padx=4)

        qutip_box = ttk.Labelframe(
            right, text="Independent cross-check (QuTiP)", style="Section.TLabelframe"
        )
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
        self.btn_check_analytic = ttk.Button(
            qbtns,
            text="AISim vs analytic (no deps)",
            command=lambda: self._run_validation_check("analytic"),
        )
        self.btn_check_analytic.pack(side=LEFT, padx=(0, 6))
        self.btn_check_qutip = ttk.Button(
            qbtns,
            text="Full QuTiP cross-check",
            command=lambda: self._run_validation_check("qutip"),
        )
        self.btn_check_qutip.pack(side=LEFT, padx=6)
        ttk.Label(qbtns, textvariable=self.validation_status_var, foreground="#5b6880").pack(
            side=LEFT, padx=12
        )

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
                "",
                END,
                iid=key,
                text=key,
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
                    module=mod,
                    published=published,
                    predicted=predicted,
                    ratio=ratio,
                    tol=tol,
                    within=(1.0 / tol) <= ratio <= tol,
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
                self.repro_tree.insert(
                    "",
                    END,
                    iid=row["suffix"],
                    text=f"{row['label']} (unavailable)",
                    values=("—", "—", "—", "—"),
                )
                continue
            self.repro_tree.insert(
                "",
                END,
                iid=row["suffix"],
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
        self._append_log(
            self.live_summary, f"Loaded {row['label']} reproduction config into the editor."
        )
        if run_after:
            self.notebook.select(0)
            self.run_async()
        else:
            self.notebook.select(2)
            self.validation_status_var.set(
                f"Loaded {row['label']}. Press 'Run Pipeline' (top right) to reproduce it."
            )

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
            self._queue.put(
                (
                    "validation",
                    "QuTiP is not installed.\n"
                    "  Install it with:   pip install qgrav[qutip]\n"
                    "  The 'AISim vs analytic' check needs no extra packages and works now.\n",
                )
            )
        except Exception as exc:  # pragma: no cover - defensive
            self._queue.put(("validation", f"Cross-check failed: {exc}\n"))
