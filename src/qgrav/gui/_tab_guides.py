"""Guides tab: authored guide topics and project-document links.

Moved verbatim out of ``app.py`` (v1.4 modularisation).
"""

from __future__ import annotations

import logging
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import END, LEFT, VERTICAL, ttk
from typing import Any

logger = logging.getLogger(__name__)


class GuidesTabMixin:
    """Guides tab: authored guide topics and project-document links.

    Mixed into :class:`qgrav.gui.app.QGravApp`, which owns every shared
    ``self`` attribute (Tk variables, ``_queue``, ``_project_root``, ...)
    created in ``QGravApp.__init__``. Worker threads must communicate
    only via ``self._queue.put(...)`` - never touch Tk widgets directly
    from a thread (the Tk thread polls the queue via ``_poll_queue``).
    """

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
        self.guide_open_btn = ttk.Button(
            toolbar,
            text="Open this document externally",
            command=self._open_current_guide_doc,
            state="disabled",
        )
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
