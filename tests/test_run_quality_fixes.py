"""Regression tests for the post-fellowship run-quality fixes.

Covers: servo_settle_drops statistics, multi-drop plot specs, strict-JSON
metrics sanitisation, validation PREDICTION_BASIS labels, ignored-servo-key
warnings, gravity plot units, and log-scale simulation plot specs.
"""

from __future__ import annotations

import json
import math

import numpy as np
import pytest

from qgrav.pipeline._common import _jsonable
from qgrav.sim_ai._config_run import run_simulation_from_config
from qgrav.sim_ai._multi_drop import _allan_deviation, run_aisim_multi_drop_cycle


def _small_campaign(servo_settle_drops: int = 0) -> dict:
    return run_aisim_multi_drop_cycle(
        n_drops=24,
        cycle_time_s=1.0,
        n_atoms=400,
        detector_radius_m=2.0e-2,
        seed=7,
        gravity_propagation=False,
        detection_noise_enabled=False,
        servo_enabled=True,
        servo_type="integrator",
        servo_settle_drops=servo_settle_drops,
    )


class TestServoSettleDrops:
    def test_default_preserves_historical_behaviour(self):
        res = _small_campaign(servo_settle_drops=0)
        g = np.asarray(res["g_estimates_m_s2"])
        assert res["servo_settle_drops"] == 0
        assert res["mean_g_m_s2"] == pytest.approx(float(np.mean(g)))
        assert res["std_g_m_s2"] == pytest.approx(float(np.std(g)))

    def test_settle_excluded_from_statistics_only(self):
        settle = 8
        res0 = _small_campaign(servo_settle_drops=0)
        res = _small_campaign(servo_settle_drops=settle)
        g0 = np.asarray(res0["g_estimates_m_s2"])
        g = np.asarray(res["g_estimates_m_s2"])
        # The full per-drop series is unchanged: the parameter only affects
        # which drops enter the summary statistics.
        np.testing.assert_allclose(g, g0)
        assert res["servo_settle_drops"] == settle
        assert res["mean_g_m_s2"] == pytest.approx(float(np.mean(g[settle:])))
        assert res["std_g_m_s2"] == pytest.approx(float(np.std(g[settle:])))
        taus_ref, adev_ref = _allan_deviation(g[settle:], 1.0)
        np.testing.assert_allclose(np.asarray(res["allan_taus_s"]), taus_ref)
        np.testing.assert_allclose(np.asarray(res["allan_dev_m_s2"]), adev_ref)

    def test_settle_clamped_below_n_drops(self):
        res = _small_campaign(servo_settle_drops=10_000)
        assert res["servo_settle_drops"] == 24 - 1
        assert math.isfinite(res["mean_g_m_s2"])


class TestMultiDropPlotSpecs:
    def test_plot_specs_and_derived_series(self):
        res = _small_campaign()
        names = [spec["name"] for spec in res["plot_specs"]]
        assert names == ["simulation_primary", "simulation_secondary"]
        assert len(res["g_deviation_ugal"]) == 24
        assert len(res["allan_dev_ugal"]) == len(res["allan_taus_s"])
        assert len(res["allan_white_noise_guide_ugal"]) == len(res["allan_taus_s"])
        secondary = res["plot_specs"][1]
        assert secondary["xscale"] == "log"
        assert secondary["yscale"] == "log"
        # Every series key must resolve to an array in the result (the pipeline
        # saves them under the sim_ prefix that the plot renderers read).
        for spec in res["plot_specs"]:
            assert spec["x_key"] in res
            for series in spec["series"]:
                assert series["key"] in res

    def test_detection_noise_equivalent_atoms_alias(self):
        res = run_aisim_multi_drop_cycle(
            n_drops=4,
            n_atoms=400,
            detector_radius_m=2.0e-2,
            seed=3,
            gravity_propagation=False,
            detection_noise_enabled=True,
            detection_sigma_p=6.0e-3,
        )
        assert res["detection_noise_equivalent_atoms"] == res["n_detected_effective"]
        assert res["n_detected_effective"] == int(round(1.0 / 6.0e-3**2))


class TestStrictJsonMetrics:
    def test_nonfinite_floats_become_null(self):
        obj = {
            "nan": float("nan"),
            "inf": float("inf"),
            "np_nan": np.float64("nan"),
            "arr": np.array([1.0, np.nan, np.inf]),
            "nested": {"v": [float("-inf"), 2.0]},
            "ok": 1.5,
        }
        out = _jsonable(obj)
        assert out["nan"] is None
        assert out["inf"] is None
        assert out["np_nan"] is None
        assert out["arr"] == [1.0, None, None]
        assert out["nested"]["v"] == [None, 2.0]
        assert out["ok"] == 1.5
        # The sanitised structure must serialise under strict JSON rules.
        json.dumps(out, allow_nan=False)


class TestPredictionBasis:
    def test_all_setups_declare_basis(self):
        from qgrav.validation import (
            freier_2016_setup,
            hu_2013_setup,
            menoret_2018_setup,
            wu_2019_setup,
            xu_2022_setup,
        )

        assert freier_2016_setup.PREDICTION_BASIS == "independent"
        assert hu_2013_setup.PREDICTION_BASIS == "independent"
        assert menoret_2018_setup.PREDICTION_BASIS == "anchored"
        assert xu_2022_setup.PREDICTION_BASIS == "anchored"
        assert wu_2019_setup.PREDICTION_BASIS == "anchored"

    def test_anchored_setups_reproduce_target_by_construction(self):
        """Document the anchoring: for anchored setups the 'prediction' IS the
        published value, so the regression checks pipeline consistency, not
        noise physics."""
        from qgrav.validation import menoret_2018_setup, wu_2019_setup, xu_2022_setup
        from qgrav.validation.menoret_2018_setup import MENORET_2018_NOISE_BUDGET
        from qgrav.validation.wu_2019_setup import WU_2019_TARGETS
        from qgrav.validation.xu_2022_setup import XU_2022_TARGETS

        assert menoret_2018_setup.predicted_short_term_asd_m_s2_per_sqrt_hz() == pytest.approx(
            MENORET_2018_NOISE_BUDGET["campaign_g_noise_target_m_s2_per_sqrt_hz"]
        )
        assert xu_2022_setup.predicted_short_term_asd_m_s2_per_sqrt_hz() == pytest.approx(
            XU_2022_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
        )
        assert wu_2019_setup.predicted_short_term_asd_m_s2_per_sqrt_hz() == pytest.approx(
            WU_2019_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
        )


class TestConfigDispatch:
    _BASE_CFG = {
        "enabled": True,
        "backend": "aisim",
        "model": "multi_drop_cycle",
        "n_atoms": 400,
        "detector_radius_m": 2.0e-2,
        "n_drops": 6,
        "seed": 5,
        "gravity_propagation": False,
        "detection_noise_enabled": False,
        "servo_enabled": True,
        "servo_type": "integrator",
    }

    def test_servo_settle_drops_passes_through(self):
        cfg = dict(self._BASE_CFG, servo_settle_drops=2)
        res = run_simulation_from_config(cfg)
        assert res is not None
        assert res["servo_settle_drops"] == 2

    def test_ignored_pid_keys_warn_for_integrator(self, caplog):
        cfg = dict(self._BASE_CFG, servo_ki=0.3)
        with caplog.at_level("WARNING", logger="qgrav.sim_ai._config_run"):
            run_simulation_from_config(cfg)
        assert any("servo_ki" in rec.getMessage() for rec in caplog.records)

    def test_ignored_gain_warns_for_pid(self, caplog):
        cfg = dict(self._BASE_CFG, servo_type="pid", servo_gain=0.5)
        with caplog.at_level("WARNING", logger="qgrav.sim_ai._config_run"):
            run_simulation_from_config(cfg)
        assert any("servo_gain" in rec.getMessage() for rec in caplog.records)


class TestGravityPlotUnits:
    def _bundle(self, units):
        n = 64
        rng = np.random.default_rng(1)
        x = rng.normal(size=n)
        t = np.arange(n) * 3600.0
        metrics = {
            "bench_type": "real_gravity",
            "sample_rate_hz": 1.0 / 3600.0,
            "psd_method": "welch",
            "welch_nperseg": 32,
            "welch_noverlap": 16,
            "station_code": "test",
        }
        if units is not None:
            metrics["series_units"] = units
        arrays = {
            "t_full": t,
            "gravity_residual_full": x,
            "t": t,
            "gravity_residual": x,
            "allan_taus": np.array([3600.0, 7200.0]),
            "allan_series": np.array([1.0, 0.7]),
        }
        return {"run_dir": None, "metrics": metrics, "summary": "", "arrays": arrays}

    def test_units_appear_in_labels(self):
        from qgrav.visuals import build_run_figure

        fig = build_run_figure(self._bundle("nm/s^2"), "gravity_series")
        assert "nm/s^2" in fig.axes[0].get_ylabel()
        fig = build_run_figure(self._bundle("nm/s^2"), "allan")
        assert "nm/s^2" in fig.axes[0].get_ylabel()

    def test_missing_units_fall_back(self):
        from qgrav.visuals import build_run_figure

        fig = build_run_figure(self._bundle(None), "gravity_series")
        assert "dataset units" in fig.axes[0].get_ylabel()


class TestSimPlotSpecScales:
    def test_log_scale_applied(self):
        from matplotlib.figure import Figure

        from qgrav.visuals import _plot_sim_from_spec

        arrays = {
            "sim_x": np.array([1.0, 10.0, 100.0]),
            "sim_y": np.array([1.0, 0.3, 0.1]),
        }
        spec = {
            "x_key": "x",
            "xscale": "log",
            "yscale": "log",
            "series": [{"key": "y", "label": "y", "kind": "line"}],
        }
        fig = Figure()
        ax = fig.add_subplot(111)
        _plot_sim_from_spec(ax, arrays, spec)
        assert ax.get_xscale() == "log"
        assert ax.get_yscale() == "log"

    def test_linear_default_unchanged(self):
        from matplotlib.figure import Figure

        from qgrav.visuals import _plot_sim_from_spec

        arrays = {"sim_x": np.array([1.0, 2.0]), "sim_y": np.array([1.0, 2.0])}
        spec = {"x_key": "x", "series": [{"key": "y", "label": "y", "kind": "line"}]}
        fig = Figure()
        ax = fig.add_subplot(111)
        _plot_sim_from_spec(ax, arrays, spec)
        assert ax.get_xscale() == "linear"
        assert ax.get_yscale() == "linear"


class TestVibrationWrappedPhase:
    def test_wrapped_phase_in_range(self):
        from qgrav.sim_ai._sweeps import run_aisim_vibration_sensitivity_sweep

        res = run_aisim_vibration_sensitivity_sweep(
            n_atoms=400,
            detector_radius_m=2.0e-2,
            seed=2,
            n_amplitude_points=5,
            amplitude_max_m=1.0e-8,
        )
        wrapped = res["phase_bias_wrapped_rad"]
        assert -math.pi < wrapped <= math.pi
        # Wrapped and raw agree modulo 2*pi.  The raw bias is ~1e7 rad, so
        # double-precision rounding leaves a residual of order 1e-9 rad.
        raw = res["phase_bias_rad"]
        assert math.isclose(math.remainder(raw - wrapped, 2.0 * math.pi), 0.0, abs_tol=1e-6)
