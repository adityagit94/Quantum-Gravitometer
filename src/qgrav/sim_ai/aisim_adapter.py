"""Facade for the AISim adapter layer.

Until v1.4 this module held the entire adapter (~2,000 lines). It is now a
thin facade over the private split modules so every historical import path
keeps working, including the private helpers tests rely on:

- :mod:`qgrav.sim_ai._adapter_core` - shared helpers, scope labels,
  ``_pack_result``, MZ sequence runners, Bertoldi finite-tau scale factor
- :mod:`qgrav.sim_ai._scans` - Rabi scan + MZ phase scan
- :mod:`qgrav.sim_ai._sweeps` - gravity sweep + vibration-sensitivity sweep
- :mod:`qgrav.sim_ai._multi_drop` - multi-drop measurement cycle
- :mod:`qgrav.sim_ai._config_run` - ``run_simulation_from_config`` dispatcher

The physics did not change; the code moved verbatim.
"""

from __future__ import annotations

from qgrav.sim_ai._adapter_core import (  # noqa: F401
    _ALLOWED_STUDY_SCOPE_CATEGORIES,
    STUDY_SCOPE_ANALYTICAL_ONLY,
    STUDY_SCOPE_FULLY_SIMULATED,
    STUDY_SCOPE_HYBRID,
    _build_wavefront,
    _calibrate_gravity_phase_and_visibility,
    _calibrate_gravity_phase_offset,
    _classify_study_scope,
    _coerce_zernike_coeffs,
    _create_detected_ensemble,
    _fit_sinusoid,
    _gaussian_beam,
    _hybrid_gravity_phase_rad,
    _import_aisim,
    _pack_result,
    _run_mach_zehnder_sequence,
    _run_mach_zehnder_sequence_with_gravity,
    _vibration_phase_sinusoid,
    _wave_vectors,
    bertoldi_finite_tau_scale_factor,
    is_aisim_available,
)
from qgrav.sim_ai._aisim_overrides import (  # noqa: F401
    ChirpedWavevectors,
    GravityFreePropagator,
    IntegratedPhaseSpatialSuperpositionTransitionPropagator,
)
from qgrav.sim_ai._config_run import run_simulation_from_config  # noqa: F401
from qgrav.sim_ai._multi_drop import (  # noqa: F401
    _allan_deviation,
    _multi_drop_noise_description,
    run_aisim_multi_drop_cycle,
)
from qgrav.sim_ai._scans import (  # noqa: F401
    run_aisim_mach_zehnder_phase_scan,
    run_aisim_rabi_scan,
)
from qgrav.sim_ai._sweeps import (  # noqa: F401
    run_aisim_gravity_sweep,
    run_aisim_vibration_sensitivity_sweep,
)

__all__ = [
    "STUDY_SCOPE_ANALYTICAL_ONLY",
    "STUDY_SCOPE_FULLY_SIMULATED",
    "STUDY_SCOPE_HYBRID",
    "ChirpedWavevectors",
    "GravityFreePropagator",
    "IntegratedPhaseSpatialSuperpositionTransitionPropagator",
    "bertoldi_finite_tau_scale_factor",
    "is_aisim_available",
    "run_aisim_gravity_sweep",
    "run_aisim_mach_zehnder_phase_scan",
    "run_aisim_multi_drop_cycle",
    "run_aisim_rabi_scan",
    "run_aisim_vibration_sensitivity_sweep",
    "run_simulation_from_config",
]
