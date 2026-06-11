"""Data Browser tab: dataset scanning, station preview figure, and
creating real-gravity configs from the selection.

Moved verbatim out of ``app.py`` (v1.4 modularisation).
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import END, LEFT, VERTICAL, X, filedialog, messagebox, ttk
from typing import Any

import numpy as np
import yaml
from matplotlib.figure import Figure

from qgrav.bench_ifo import load_real_gravity
from qgrav.datasets import list_stations_in_source
from qgrav.metrics import allan_deviation_overlapping, compute_psd

logger = logging.getLogger(__name__)


class DataBrowserTabMixin:
    """Data Browser tab: dataset scanning, station preview figure, and
    creating real-gravity configs from the selection.

        Mixed into :class:`qgrav.gui.app.QGravApp`, which owns every shared
        ``self`` attribute (Tk variables, ``_queue``, ``_project_root``, ...)
        created in ``QGravApp.__init__``. Worker threads must communicate
        only via ``self._queue.put(...)`` - never touch Tk widgets directly
        from a thread (the Tk thread polls the queue via ``_poll_queue``).
    """

    # Declared so the type matches QGravApp.__init__ (None until a station
    # preview loads).
    _browser_data: dict[str, Any] | None

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
        ttk.Entry(row, textvariable=self.browser_dataset_var).grid(
            row=0, column=1, sticky="ew", padx=8
        )
        ttk.Button(row, text="Browse", command=self._browse_dataset_source).grid(
            row=0, column=2, padx=4
        )
        ttk.Button(row, text="Scan", command=self.scan_dataset_source).grid(row=0, column=3, padx=4)
        ttk.Button(row, text="Use sample", command=self._load_sample_dataset).grid(
            row=0, column=4, padx=4
        )
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
        self.station_tree = ttk.Treeview(
            tree_frame, columns=("lon", "lat"), show="tree headings", height=18
        )
        self.station_tree.heading("#0", text="Station")
        self.station_tree.heading("lon", text="Longitude")
        self.station_tree.heading("lat", text="Latitude")
        self.station_tree.column("#0", width=110, stretch=True)
        self.station_tree.column("lon", width=90)
        self.station_tree.column("lat", width=90)
        self.station_tree.grid(row=0, column=0, sticky="nsew")
        station_tree_scroll = ttk.Scrollbar(
            tree_frame, orient=VERTICAL, command=self.station_tree.yview
        )
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
        station_info_scroll = ttk.Scrollbar(
            info_frame, orient=VERTICAL, command=self.station_info.yview
        )
        station_info_scroll.grid(row=0, column=1, sticky="ns")
        self.station_info.configure(yscrollcommand=station_info_scroll.set)
        controls = ttk.Frame(info_box)
        controls.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        ttk.Button(controls, text="Preview selected", command=self.preview_selected_station).pack(
            side=LEFT, padx=4
        )
        ttk.Button(
            controls, text="Create config", command=self.create_real_gravity_config_from_selection
        ).pack(side=LEFT, padx=4)
        ttk.Button(
            controls, text="Use in Setup", command=self._use_browser_selection_for_gravity
        ).pack(side=LEFT, padx=4)

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
            self.station_tree.insert(
                "",
                END,
                text=item["station_code"],
                values=(item.get("longitude_deg"), item.get("latitude_deg")),
            )
        self.station_info.delete("1.0", END)
        self.station_info.insert(
            "1.0", f"Loaded {len(stations)} stations from {source}\nSelect a station to preview.\n"
        )

    def _on_station_selected(self) -> None:
        selected = self.station_tree.selection()
        if not selected:
            return
        item = self.station_tree.item(selected[0])
        code = str(item["text"])
        self.browser_station_var.set(code)
        self.station_info.delete("1.0", END)
        self.station_info.insert(
            "1.0",
            f"Station: {code}\nLongitude: {item['values'][0]}\nLatitude: {item['values'][1]}\n",
        )

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
        psd = compute_psd(
            x,
            fs,
            method="welch",
            nperseg=min(max(8, len(x) // 4), len(x)),
            noverlap=max(1, min(len(x) // 8, len(x) // 4 - 1)),
        )

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
            data = load_real_gravity(
                source_path=source, station_code=station, segment_strategy="longest_contiguous"
            )
        except Exception as exc:
            messagebox.showerror("qgrav", str(exc))
            return
        self._browser_data = data
        fig = self._build_station_preview_figure(data)
        self._render_figure(
            fig,
            canvas_attr="_browser_canvas",
            toolbar_attr="_browser_toolbar",
            frame=self.browser_plot_frame,
            toolbar_frame=self.browser_toolbar_frame,
        )
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
            "bench_real_gravity": {
                "source_path": source,
                "station_code": station,
                "segment_strategy": "longest_contiguous",
            },
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
        self.current_context_var.set(
            "Data Browser selection copied into Setup. Apply controls to editor or run directly."
        )
