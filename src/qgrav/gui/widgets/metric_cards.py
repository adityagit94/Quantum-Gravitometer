from __future__ import annotations

import tkinter as tk
from tkinter import X, ttk
from typing import Any


class MetricCards(ttk.Frame):
    def __init__(self, master: tk.Misc) -> None:
        super().__init__(master)
        self.vars: dict[str, tk.StringVar] = {}
        self._build()

    def _add_card(self, parent: ttk.Frame, title: str, key: str, column: int) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.grid(row=0, column=column, padx=6, pady=6, sticky="nsew")
        ttk.Label(card, text=title, style="CardTitle.TLabel").pack(anchor="w")
        var = tk.StringVar(value="—")
        self.vars[key] = var
        ttk.Label(card, textvariable=var, style="CardValue.TLabel").pack(anchor="w", pady=(6, 0))

    def _build(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=X, expand=True)
        for col in range(6):
            row.columnconfigure(col, weight=1)
        self._add_card(row, "Bench", "bench", 0)
        self._add_card(row, "Station", "station", 1)
        self._add_card(row, "Allan", "backend", 2)
        self._add_card(row, "RMSE Δ", "rmse", 3)
        self._add_card(row, "Allan Δ", "allan", 4)
        self._add_card(row, "AISim peak", "aisim_peak", 5)

    def update_from_metrics(self, metrics: dict[str, Any]) -> None:
        self.vars["bench"].set(str(metrics.get("bench_type", "—")))
        self.vars["station"].set(str(metrics.get("station_code", "—")))
        self.vars["backend"].set(
            f"{metrics.get('allan_backend_used', '—')} / {metrics.get('allan_data_type', '—')}"
        )
        rmse = metrics.get("rmse_improvement_percent")
        self.vars["rmse"].set("—" if rmse is None else f"{rmse:.2f}%")
        allan = metrics.get("allan_improvement_percent_mean")
        self.vars["allan"].set("—" if allan is None else f"{allan:.2f}%")
        sim_raw = metrics.get("simulation")
        sim = sim_raw if isinstance(sim_raw, dict) else {}
        peak = sim.get("peak_excited_fraction")
        self.vars["aisim_peak"].set("—" if peak is None else f"{peak:.3f}")
