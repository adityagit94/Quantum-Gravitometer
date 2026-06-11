"""Results & Visuals tab: metrics tree, embedded matplotlib figure,
plot refresh, and run-artifact shortcuts.

Moved verbatim out of ``app.py`` (v1.4 modularisation).
"""

from __future__ import annotations

import logging
import tkinter as tk
import webbrowser
from tkinter import END, LEFT, VERTICAL, messagebox, ttk
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from qgrav.visuals import build_run_figure

logger = logging.getLogger(__name__)


class ResultsTabMixin:
    """Results & Visuals tab: metrics tree, embedded matplotlib figure,
    plot refresh, and run-artifact shortcuts.

        Mixed into :class:`qgrav.gui.app.QGravApp`, which owns every shared
        ``self`` attribute (Tk variables, ``_queue``, ``_project_root``, ...)
        created in ``QGravApp.__init__``. Worker threads must communicate
        only via ``self._queue.put(...)`` - never touch Tk widgets directly
        from a thread (the Tk thread polls the queue via ``_poll_queue``).
    """

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
        for label, cmd in [
            ("Open HTML", self.open_report),
            ("Run folder", self.open_run_folder),
            ("Metrics JSON", self.open_metrics_file),
            ("Summary", self.open_summary_file),
        ]:
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
        metrics_scroll_y = ttk.Scrollbar(
            metrics_frame, orient=VERTICAL, command=self.metrics_tree.yview
        )
        metrics_scroll_y.grid(row=0, column=1, sticky="ns")
        metrics_scroll_x = ttk.Scrollbar(
            metrics_frame, orient="horizontal", command=self.metrics_tree.xview
        )
        metrics_scroll_x.grid(row=1, column=0, sticky="ew")
        self.metrics_tree.configure(
            yscrollcommand=metrics_scroll_y.set, xscrollcommand=metrics_scroll_x.set
        )

        visuals_box = ttk.Labelframe(right, text="Interactive visuals", style="Section.TLabelframe")
        visuals_box.grid(row=0, column=0, sticky="nsew")
        visuals_box.rowconfigure(3, weight=1)
        visuals_box.columnconfigure(0, weight=1)
        ttk.Label(
            visuals_box, textvariable=self.plot_title_var, foreground="#5b6880", wraplength=760
        ).grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 4))
        top = ttk.Frame(visuals_box)
        top.grid(row=1, column=0, sticky="ew", padx=6)
        ttk.Label(top, text="Plot:").pack(side=LEFT)
        self.plot_kind_combo = ttk.Combobox(
            top, textvariable=self.plot_kind_var, values=["dashboard"], state="readonly", width=22
        )
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

    def _render_figure(
        self,
        fig: Figure,
        *,
        canvas_attr: str,
        toolbar_attr: str,
        frame: ttk.Frame,
        toolbar_frame: ttk.Frame | None = None,
    ) -> None:
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
        self.plot_title_var.set(
            f"{plot_name}: {descriptions.get(plot_name, 'Interactive plot view.')}"
        )
        self._render_figure(
            fig,
            canvas_attr="_current_canvas",
            toolbar_attr="_current_toolbar",
            frame=self.plot_frame,
            toolbar_frame=self.plot_toolbar_frame,
        )

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
