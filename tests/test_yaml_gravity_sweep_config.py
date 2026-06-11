"""v1.2.2 — full gravity-sweep / MZ-phase-scan YAML exposure.

Verifies the single_photon_detuning_hz + wavefront_zernike_coeffs +
wavefront_radius_m keys round-trip through run_simulation_from_config for the
gravity_sweep and mach_zehnder_phase_scan models, and that they actually
change the simulated output (not silently ignored).
"""

from __future__ import annotations

import numpy as np

from qgrav.sim_ai.aisim_adapter import (
    _coerce_zernike_coeffs,
    run_simulation_from_config,
)


def _gs_cfg(**overrides):
    cfg = dict(
        enabled=True,
        backend="aisim",
        model="gravity_sweep",
        n_atoms=150,
        seed=3,
        n_gravity_points=7,
        gravity_span_m_s2=4e-6,
        interferometer_time_s=0.05,
        tau_pi_half_s=23e-6,
        lock_to_midfringe=True,
        gravity_propagation=False,
    )
    cfg.update(overrides)
    return cfg


class TestZernikeCoercion:
    def test_string_keys_coerced_to_int(self):
        out = _coerce_zernike_coeffs({"4": 0.5, "8": "1.0"})
        assert out == {4: 0.5, 8: 1.0}
        assert all(isinstance(k, int) for k in out)

    def test_empty_returns_none(self):
        assert _coerce_zernike_coeffs(None) is None
        assert _coerce_zernike_coeffs({}) is None


class TestGravitySweepYAML:
    def test_single_photon_detuning_via_yaml_changes_output(self):
        base = run_simulation_from_config(_gs_cfg())
        shifted = run_simulation_from_config(_gs_cfg(single_photon_detuning_hz=1e3))
        # A strong AC-Stark shift must change the fringe (port-3 populations).
        assert not np.allclose(base["output_port_3"], shifted["output_port_3"], atol=1e-6)

    def test_wavefront_via_yaml_changes_output(self):
        base = run_simulation_from_config(_gs_cfg(n_atoms=200, temp_xy_K=5e-6))
        aberr = run_simulation_from_config(
            _gs_cfg(
                n_atoms=200,
                temp_xy_K=5e-6,
                wavefront_zernike_coeffs={4: 8.0, 8: 8.0},
                wavefront_radius_m=0.05,
            )
        )
        assert not np.allclose(base["output_port_3"], aberr["output_port_3"], atol=1e-6)

    def test_wavefront_string_keys_accepted(self):
        # YAML often yields string keys; must not raise.
        result = run_simulation_from_config(
            _gs_cfg(
                n_atoms=120,
                wavefront_zernike_coeffs={"4": 2.0},
            )
        )
        assert result is not None
        assert result["model"] == "gravity_sweep"


class TestMachZehnderPhaseScanYAML:
    def test_mz_phase_scan_single_photon_via_yaml(self):
        cfg = dict(
            enabled=True,
            backend="aisim",
            model="mach_zehnder_phase_scan",
            n_atoms=150,
            seed=3,
            n_phase_points=11,
            interferometer_time_s=0.05,
            tau_pi_half_s=23e-6,
        )
        base = run_simulation_from_config(dict(cfg))
        shifted = run_simulation_from_config(dict(cfg, single_photon_detuning_hz=1e3))
        assert not np.allclose(base["output_port_3"], shifted["output_port_3"], atol=1e-6)
