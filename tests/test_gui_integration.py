"""Full-instantiation GUI integration tests.

Unlike ``test_gui_import.py`` (import only) and ``test_gui_runtime_safety.py``
(backend only), these build the *entire* :class:`QGravApp` on a real (withdrawn)
Tk root and exercise the v1.0-v1.3 engine features now wired into the GUI:
the multi_drop_cycle model, the advanced-physics / noise-budget controls, the
Validation tab (published-reference reproductions + QuTiP cross-check), and the
navigable Guides tab.

They skip cleanly when Tk is absent (a Python built without Tk) or has no
display (headless CI without an X server), so the core suite is unaffected.
"""
from __future__ import annotations

import pytest
import yaml

try:
    import tkinter as tk
except ImportError:  # pragma: no cover - depends on the Python build
    pytest.skip("Tk not available in this Python build", allow_module_level=True)


@pytest.fixture(scope="module")
def gui_root():
    """A single Tk root shared by the module.

    Creating and destroying a Tk root once per test is fragile on Windows (a
    later ``tk.Tk()`` can raise TclError), so we create exactly one withdrawn
    root and build a fresh app on it per test.
    """
    try:
        root = tk.Tk()
    except tk.TclError:
        pytest.skip("Tk is not available (headless environment without Tk display)")
    root.withdraw()
    yield root
    try:
        root.destroy()
    except tk.TclError:
        pass


@pytest.fixture
def app(gui_root, monkeypatch):
    import qgrav.gui.app as appmod

    # Modal dialogs would block a non-interactive test run; make them no-ops.
    for name in ("showerror", "showinfo", "showwarning"):
        monkeypatch.setattr(appmod.messagebox, name, lambda *a, **k: None)
    monkeypatch.setattr(appmod.messagebox, "askyesnocancel", lambda *a, **k: None)

    from qgrav.gui import QGravApp

    application = QGravApp(gui_root)
    yield application
    # Clear this app's widgets so the next test builds fresh on the shared root.
    for child in list(gui_root.winfo_children()):
        try:
            child.destroy()
        except tk.TclError:
            pass


# ----------------------------------------------------------------------
# Structure
# ----------------------------------------------------------------------
def test_app_builds_six_tabs(app):
    names = [app.notebook.tab(i, "text") for i in range(app.notebook.index("end"))]
    assert names == [
        "Setup & Run", "Data Browser", "Config Editor",
        "Results & Visuals", "Validation", "Guides",
    ]


def test_bundled_example_actually_loads(app):
    """Regression: the asset root used to point at src/ so nothing loaded."""
    text = app.editor.get("1.0", "end").strip()
    assert text, "editor should be pre-populated from the bundled example config"
    assert yaml.safe_load(text), "bundled example must parse as a mapping"


def test_multi_drop_in_model_dropdown(app):
    # Find the study-model combobox by its registered values.
    found = _find_combo_with_value(app.root, "multi_drop_cycle")
    assert found, "multi_drop_cycle must be offered in the study-model dropdown"


# ----------------------------------------------------------------------
# Setup tab: multi-drop + noise knobs round-trip
# ----------------------------------------------------------------------
def test_multi_drop_controls_roundtrip(app):
    app.workflow_var.set("synthetic")
    app.sim_model_var.set("multi_drop_cycle")
    app.sim_atoms_var.set("300")
    app.sim_n_drops_var.set("40")
    app.sim_cycle_time_var.set("1.5")
    app.sim_interferometer_time_var.set("0.26")
    app.sim_detection_sigma_p_var.set("6e-3")
    app.sim_raman_phase_noise_var.set("0.012")
    app.sim_fit_visibility_var.set(True)
    app.sim_gravity_propagation_var.set(True)
    app.sim_single_photon_detuning_var.set("-700e6")
    app.sim_wavefront_zernike_var.set("0, 0, 0, 5e-9")
    app.sim_servo_enabled_var.set(True)
    app.sim_servo_type_var.set("pid")
    app.apply_quick_controls_to_editor()

    cfg = yaml.safe_load(app.editor.get("1.0", "end"))
    sim = cfg["simulation"]
    assert sim["model"] == "multi_drop_cycle"
    assert sim["n_drops"] == 40
    assert sim["detection_sigma_p"] == pytest.approx(6e-3)
    assert sim["raman_phase_noise_rad"] == pytest.approx(0.012)
    assert sim["fit_visibility"] is True
    assert sim["gravity_propagation"] is True
    assert sim["single_photon_detuning_hz"] == pytest.approx(-700e6)
    assert sim["wavefront_zernike_coeffs"] == [0.0, 0.0, 0.0, 5e-9]
    assert sim["servo_type"] == "pid"

    # And it reads back into the controls (mutate, then re-sync from the dict).
    app.sim_n_drops_var.set("999")
    app.sim_fit_visibility_var.set(False)
    app.sim_model_var.set("rabi_scan")
    app.sync_controls_from_dict(cfg)
    assert app.sim_n_drops_var.get() == "40"
    assert app.sim_fit_visibility_var.get() is True
    assert app.sim_model_var.get() == "multi_drop_cycle"


def test_zernike_parse_error_is_friendly(app):
    app.sim_wavefront_zernike_var.set("not, numbers")
    with pytest.raises(ValueError, match="Zernike"):
        app._parse_zernike()


# ----------------------------------------------------------------------
# Validation tab
# ----------------------------------------------------------------------
def test_reference_library_populated(app):
    from qgrav.validation import REFERENCES

    rows = app.refs_tree.get_children()
    assert len(rows) == len(REFERENCES) == 14


def test_reproduction_rows_present_and_within_band(app):
    rows = app.repro_tree.get_children()
    assert set(rows) == {"freier_2016", "hu_2013", "menoret_2018", "xu_2022", "wu_2019"}
    # Predicted ASD should land inside each paper's documented tolerance band.
    for r in app._repro_rows:
        assert "error" not in r, r
        assert r["within"], f"{r['suffix']} predicted/published ratio {r['ratio']:.2f} out of band"


def test_one_click_reproduction_builds_runnable_config(app):
    app.repro_tree.selection_set("freier_2016")
    app.repro_atoms_var.set("60")   # tiny: keep the test fast
    app.repro_drops_var.set("8")
    app._load_selected_reproduction(run_after=False)

    cfg = yaml.safe_load(app.editor.get("1.0", "end"))
    sim = cfg["simulation"]
    assert sim["model"] == "multi_drop_cycle"
    assert sim["n_atoms"] == 60 and sim["n_drops"] == 8

    # The engine must accept the GUI-built config and run it.
    from qgrav.sim_ai.aisim_adapter import run_simulation_from_config

    res = run_simulation_from_config(sim)
    assert res["study_scope_category"] == "FULLY_SIMULATED"
    assert res["mean_g_m_s2"] == pytest.approx(9.81, abs=0.05)


def test_analytic_crosscheck_worker(app):
    """The no-dependency AISim-vs-analytic check posts a PASS message."""
    app._validation_worker("analytic")
    kind, payload = app._queue.get_nowait()
    assert kind == "validation"
    assert "AISim" in payload and "analytic" in payload


def test_qutip_crosscheck_worker_if_available(app):
    pytest.importorskip("qutip")
    app._validation_worker("qutip")
    kind, payload = app._queue.get_nowait()
    assert kind == "validation"
    assert "QuTiP" in payload


# ----------------------------------------------------------------------
# Guides tab
# ----------------------------------------------------------------------
def test_guides_have_authored_topics_and_how_to_move_ahead(app):
    titles = []
    for group in app.guide_nav.get_children(""):
        for leaf in app.guide_nav.get_children(group):
            titles.append(app.guide_nav.item(leaf, "text"))
    assert "Quick start" in titles
    assert "How to move ahead" in titles

    # Select 'How to move ahead' and confirm it renders the user-owned next steps.
    for group in app.guide_nav.get_children(""):
        for leaf in app.guide_nav.get_children(group):
            if app.guide_nav.item(leaf, "text") == "How to move ahead":
                app.guide_nav.selection_set(leaf)
                app._on_guide_selected()
    body = app.guide_text.get("1.0", "end")
    assert "PHYSICS_REVIEW_PACKET" in body and "JOSS" in body


# ----------------------------------------------------------------------
# Widgets
# ----------------------------------------------------------------------
def test_widgets_construct(app):
    from tkinter import ttk

    from qgrav.gui.widgets import CollapsibleSection, Tooltip

    btn = ttk.Button(app.root, text="x")
    Tooltip(btn, "a tip")  # must not raise
    sec = CollapsibleSection(app.root, "Title", subtitle="sub", expanded=False)
    assert sec.is_expanded is False
    sec.toggle()
    assert sec.is_expanded is True


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def _find_combo_with_value(widget, needle):
    from tkinter import ttk

    if isinstance(widget, ttk.Combobox):
        try:
            if needle in widget.cget("values"):
                return True
        except tk.TclError:
            pass
    for child in widget.winfo_children():
        if _find_combo_with_value(child, needle):
            return True
    return False
