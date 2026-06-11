"""v1.2.3 — performance guard (runs in the normal suite, no plugin needed).

A single generous wall-clock ceiling on the core MZ sequence so an accidental
O(n^2) (or worse) regression in the hot path is caught by CI.  The ceiling is
~150x the representative time (see docs/PERFORMANCE.md), so it only fires on a
genuine algorithmic regression, never on machine-speed jitter.
"""

from __future__ import annotations

import time

from qgrav.sim_ai.aisim_adapter import (
    _create_detected_ensemble,
    _gaussian_beam,
    _run_mach_zehnder_sequence,
    _wave_vectors,
)


def test_single_mz_under_wall_clock_ceiling():
    _, atoms, _, _, _ = _create_detected_ensemble(
        n_atoms=1000,
        seed=1,
        cloud_radius_m=3e-3,
        temp_xy_K=2.5e-6,
        temp_z_K=100e-9,
        detector_time_s=778e-3,
        detector_radius_m=5e-3,
        multiport=True,
    )
    beam = _gaussian_beam(beam_radius_m=0.015, center_rabi_freq_hz=12.5e3)
    wv = _wave_vectors(wavelength_m=780.241e-9)

    # Warm up (import/JIT-free, but excludes first-call overhead).
    _run_mach_zehnder_sequence(
        atoms,
        tau_pi_half_s=23e-6,
        interferometer_time_s=0.26,
        intensity_profile=beam,
        wave_vectors=wv,
        final_phase_rad=1.0,
    )
    t0 = time.perf_counter()
    for _ in range(10):
        _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=23e-6,
            interferometer_time_s=0.26,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=1.0,
        )
    per_call = (time.perf_counter() - t0) / 10.0
    # Representative: ~1.3 ms/call (1000 atoms).  Ceiling 200 ms = ~150x margin.
    assert per_call < 0.2, (
        f"single MZ sequence took {per_call*1e3:.1f} ms/call (ceiling 200 ms) "
        f"— possible algorithmic regression in the hot path."
    )
