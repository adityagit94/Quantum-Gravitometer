"""Tests for v0.8 study-scope labelling on AISim simulation runners.

Per PRD W10/R16.4: every ``run_aisim_*`` function in
``qgrav.sim_ai.aisim_adapter`` must return a result dict containing both
the existing free-text ``study_scope`` and a canonical
``study_scope_category`` whose value is one of the allowed enum members.
"""
from __future__ import annotations

import inspect

import pytest

from qgrav.sim_ai import aisim_adapter
from qgrav.sim_ai.aisim_adapter import (
    STUDY_SCOPE_ANALYTICAL_ONLY,
    STUDY_SCOPE_FULLY_SIMULATED,
    STUDY_SCOPE_HYBRID,
    _ALLOWED_STUDY_SCOPE_CATEGORIES,
    _classify_study_scope,
)


def _aisim_runner_names() -> list[str]:
    return [
        name
        for name, obj in inspect.getmembers(aisim_adapter, inspect.isfunction)
        if name.startswith("run_aisim_") and not name.startswith("run_aisim_from")
    ]


def test_at_least_four_aisim_runners_exist():
    names = _aisim_runner_names()
    # The current set is: rabi_scan, mach_zehnder_phase_scan, gravity_sweep,
    # vibration_sensitivity_sweep.
    assert len(names) >= 4, f"unexpectedly few runners: {names}"


def test_classify_rabi_scope_is_fully_simulated():
    cat, desc = _classify_study_scope("full_aisim_two_level_population_scan")
    assert cat == STUDY_SCOPE_FULLY_SIMULATED
    assert "Fully simulated" in desc


def test_classify_mach_zehnder_phase_scan_is_fully_simulated():
    cat, _ = _classify_study_scope("full_aisim_three_pulse_phase_fringe_study")
    assert cat == STUDY_SCOPE_FULLY_SIMULATED


def test_classify_gravity_sweep_is_hybrid():
    cat, desc = _classify_study_scope("hybrid_aisim_plus_closed_form_gravity_phase")
    assert cat == STUDY_SCOPE_HYBRID
    assert "Hybrid" in desc


def test_classify_vibration_sweep_is_hybrid():
    cat, _ = _classify_study_scope("hybrid_aisim_plus_reference_mirror_vibration_phase")
    assert cat == STUDY_SCOPE_HYBRID


def test_allowed_categories_are_three():
    assert _ALLOWED_STUDY_SCOPE_CATEGORIES == {
        STUDY_SCOPE_FULLY_SIMULATED,
        STUDY_SCOPE_HYBRID,
        STUDY_SCOPE_ANALYTICAL_ONLY,
    }


def test_pack_result_propagates_category_and_description():
    """Calling _pack_result directly with a hybrid scope string adds both
    canonical fields."""
    from qgrav.sim_ai.aisim_adapter import _pack_result
    from qgrav.physics import AtomSourceConfig

    src = AtomSourceConfig(
        n_atoms_total=100, seed=0,
        cloud_radius_m=3e-3,
        temp_xy_K=1e-6, temp_z_K=1e-7,
        detector_time_s=0.7, detector_radius_m=5e-3,
        multiport=False,
    )
    out = _pack_result(
        {"summary_rows": {}},
        source_cfg=src,
        detected_count=50,
        pulse_sequence={"name": "test"},
        physical_model={"name": "test"},
        study_scope="hybrid_aisim_plus_closed_form_gravity_phase",
        limitations=["test limitation"],
    )
    assert out["study_scope_category"] == STUDY_SCOPE_HYBRID
    assert "Hybrid" in out["study_scope_description"]
    # Backwards-compat: the original free-text field is preserved.
    assert out["study_scope"] == "hybrid_aisim_plus_closed_form_gravity_phase"
