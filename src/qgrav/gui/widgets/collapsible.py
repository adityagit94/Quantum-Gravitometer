"""A collapsible (expand/collapse) section for grouping optional controls.

Used to keep the Setup form approachable: the everyday controls stay visible
while the advanced physics and noise-budget knobs live inside sections that are
collapsed by default.  Add children to the ``.body`` frame.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import X, ttk


class CollapsibleSection(ttk.Frame):
    """A labelled frame whose body can be toggled open/closed.

    Parameters
    ----------
    master:
        Parent widget.
    title:
        Header text (a ``▸``/``▾`` caret is prefixed automatically).
    expanded:
        Whether the body starts visible.
    subtitle:
        Optional one-line description shown under the header when expanded.
    """

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        *,
        expanded: bool = False,
        subtitle: str = "",
    ) -> None:
        super().__init__(master)
        self._title = title
        self._expanded = bool(expanded)
        self.columnconfigure(0, weight=1)

        self._toggle_var = tk.StringVar()
        self._header = ttk.Button(
            self,
            textvariable=self._toggle_var,
            style="Toolbutton",
            command=self.toggle,
        )
        self._header.grid(row=0, column=0, sticky="ew")

        self._container = ttk.Frame(self)
        self.body = ttk.Frame(self._container)
        self.body.pack(fill=X, expand=True, padx=4, pady=(2, 6))

        self._subtitle = subtitle
        if subtitle:
            self._subtitle_label = ttk.Label(
                self._container,
                text=subtitle,
                wraplength=430,
                foreground="#5b6880",
            )
            self._subtitle_label.pack(fill=X, anchor="w", padx=6, pady=(2, 0), before=self.body)

        self._refresh()

    def toggle(self) -> None:
        self._expanded = not self._expanded
        self._refresh()

    def set_expanded(self, expanded: bool) -> None:
        self._expanded = bool(expanded)
        self._refresh()

    @property
    def is_expanded(self) -> bool:
        return self._expanded

    def _refresh(self) -> None:
        caret = "▾" if self._expanded else "▸"
        self._toggle_var.set(f"  {caret}  {self._title}")
        if self._expanded:
            self._container.grid(row=1, column=0, sticky="ew")
        else:
            self._container.grid_forget()
