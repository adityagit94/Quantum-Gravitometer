"""A lightweight hover tooltip for Tk widgets.

Tk has no native tooltip, so this attaches ``<Enter>``/``<Leave>``/``<Motion>``
bindings to any widget and shows a small borderless ``Toplevel`` with wrapped
help text after a short delay.  It is deliberately defensive: every Tk call is
guarded so a tooltip can never crash the application (e.g. if the parent widget
is destroyed while the pointer is still over it).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class Tooltip:
    """Attach a hover tooltip to *widget*.

    Parameters
    ----------
    widget:
        The Tk/ttk widget to annotate.
    text:
        The help text to show.  Wrapped at ``wraplength`` pixels.
    delay_ms:
        How long the pointer must rest before the tip appears.
    wraplength:
        Wrap width in pixels.
    """

    def __init__(
        self,
        widget: tk.Misc,
        text: str,
        *,
        delay_ms: int = 450,
        wraplength: int = 320,
    ) -> None:
        self.widget = widget
        self.text = text
        self.delay_ms = int(delay_ms)
        self.wraplength = int(wraplength)
        self._tip: tk.Toplevel | None = None
        self._after_id: str | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        widget.bind("<Destroy>", self._hide, add="+")

    # -- scheduling --------------------------------------------------------
    def _schedule(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        try:
            self._after_id = self.widget.after(self.delay_ms, self._show)
        except tk.TclError:
            self._after_id = None

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    # -- display -----------------------------------------------------------
    def _show(self) -> None:
        if self._tip is not None or not self.text:
            return
        try:
            x = self.widget.winfo_pointerx() + 14
            y = self.widget.winfo_pointery() + 18
            tip = tk.Toplevel(self.widget)
            tip.wm_overrideredirect(True)
            tip.wm_geometry(f"+{x}+{y}")
            try:
                tip.attributes("-topmost", True)
            except tk.TclError:
                pass
            label = ttk.Label(
                tip,
                text=self.text,
                justify="left",
                background="#1f2d3d",
                foreground="#f4f8ff",
                relief="solid",
                borderwidth=1,
                padding=(8, 5),
                wraplength=self.wraplength,
                font=("Segoe UI", 9),
            )
            label.pack()
            self._tip = tip
        except tk.TclError:
            self._tip = None

    def _hide(self, _event: tk.Event | None = None) -> None:
        self._cancel()
        if self._tip is not None:
            try:
                self._tip.destroy()
            except tk.TclError:
                pass
            self._tip = None


def attach_tooltip(widget: tk.Misc, text: str, **kwargs) -> Tooltip:
    """Convenience wrapper: ``attach_tooltip(entry, "help")``."""
    return Tooltip(widget, text, **kwargs)
