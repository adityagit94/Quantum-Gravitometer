"""v1.2.3 — performance micro-benchmarks (require pytest-benchmark).

Run with:  pytest tests/benchmark_aisim.py -m benchmark
(or         pip install .[benchmark] && pytest -m benchmark)

These are excluded from the default fast suite (they need the pytest-benchmark
plugin; the module is skipped cleanly if it is absent).  See docs/PERFORMANCE.md
for representative numbers.  A lightweight wall-clock *guard* (no plugin needed)
lives in tests/test_performance_guard.py and runs in the normal suite.
"""

from __future__ import annotations

import pytest

pytest.importorskip("pytest_benchmark")

from qgrav.sim_ai.aisim_adapter import (  # noqa: E402
    _create_detected_ensemble,
    _gaussian_beam,
    _run_mach_zehnder_sequence,
    _wave_vectors,
    run_aisim_gravity_sweep,
    run_aisim_multi_drop_cycle,
)

pytestmark = pytest.mark.benchmark


def _ensemble(n_atoms=1000):
    _, atoms, _, _, _ = _create_detected_ensemble(
        n_atoms=n_atoms,
        seed=1,
        cloud_radius_m=3e-3,
        temp_xy_K=2.5e-6,
        temp_z_K=100e-9,
        detector_time_s=778e-3,
        detector_radius_m=5e-3,
        multiport=True,
    )
    return atoms


def test_benchmark_single_mz(benchmark):
    atoms = _ensemble(1000)
    beam = _gaussian_beam(beam_radius_m=0.015, center_rabi_freq_hz=12.5e3)
    wv = _wave_vectors(wavelength_m=780.241e-9)
    benchmark(
        lambda: _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=23e-6,
            interferometer_time_s=0.26,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=1.0,
        )
    )


def test_benchmark_gravity_sweep_hybrid(benchmark):
    benchmark(
        lambda: run_aisim_gravity_sweep(
            n_atoms=1000,
            seed=1,
            n_gravity_points=61,
            gravity_span_m_s2=6e-6,
            gravity_propagation=False,
        )
    )


def test_benchmark_gravity_sweep_emergent(benchmark):
    benchmark(
        lambda: run_aisim_gravity_sweep(
            n_atoms=1000,
            seed=1,
            n_gravity_points=61,
            gravity_span_m_s2=6e-6,
            gravity_propagation=True,
        )
    )


def test_benchmark_multi_drop_emergent(benchmark):
    benchmark(
        lambda: run_aisim_multi_drop_cycle(
            n_drops=100,
            n_atoms=1000,
            seed=1,
            interferometer_time_s=0.26,
            gravity_propagation=True,
        )
    )
