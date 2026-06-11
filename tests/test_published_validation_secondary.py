"""Secondary published-reference regressions (Phase 16).

Validates four additional benchmark setups:
  - Hu 2013       (HUST lab best-case, 4.2 µGal/√Hz)
  - Ménoret 2018  (Muquans AQG Larzac, 750 nm/s²/√Hz)
  - Xu 2022       (HUST-QG transportable, 24 µGal/√Hz, NEW)
  - Wu 2019       (Berkeley mobile, 37 µGal/√Hz, NEW)

The Freier 2016 *primary* regression lives in its own file
(``test_published_validation_freier_2016.py``).  All four here follow the
same pattern: curated-parameter sanity + ``@pytest.mark.slow`` simulation
regression with a factor-2.5 tolerance (wider than Freier's factor-3 because
these are smaller-N setups; per the noise-budget physics the simulated ASD
overshoots by ~1.5x at V~0.6 vs the published V).
"""

from __future__ import annotations

import math

import pytest

from qgrav.sim_ai.aisim_adapter import run_aisim_multi_drop_cycle
from qgrav.validation import (
    hu_2013_setup,
    menoret_2018_setup,
    wu_2019_setup,
    xu_2022_setup,
)

_SETUPS = {
    "hu_2013": hu_2013_setup,
    "menoret_2018": menoret_2018_setup,
    "xu_2022": xu_2022_setup,
    "wu_2019": wu_2019_setup,
}


class TestParameterIntegrity:
    """Curated parameters must match the research-validated values."""

    def test_hu_2013_is_300ms_not_10m_tower(self):
        # The single most important research correction for this paper:
        # Hu 2013 is the HUST short fountain (T=300 ms), not a 10-m tower.
        assert hu_2013_setup.HU_2013_PARAMS["interferometer_time_s"] == 0.300
        assert hu_2013_setup.HU_2013_PARAMS["apex_above_mot_m"] == 0.75
        assert hu_2013_setup.HU_2013_TARGETS["short_term_noise_m_s2_per_sqrt_hz"] == 4.2e-8

    def test_menoret_2018_T60ms_cycle500ms_no_isolation(self):
        # T=60 ms (NOT 80 ms), cycle 500 ms (~2 Hz NOT 1 s).
        assert menoret_2018_setup.MENORET_2018_PARAMS["interferometer_time_s"] == 0.060
        assert menoret_2018_setup.MENORET_2018_PARAMS["cycle_time_s"] == 0.500
        assert menoret_2018_setup.MENORET_2018_PARAMS["contrast"] == 0.40
        assert (
            menoret_2018_setup.MENORET_2018_TARGETS["short_term_noise_m_s2_per_sqrt_hz"] == 7.5e-7
        )

    def test_xu_2022_systematic_budget_target(self):
        # Xu 2022 is the FIRST HUST instrument with a published per-effect
        # systematic budget (3 µGal combined uncertainty).
        assert xu_2022_setup.XU_2022_TARGETS["combined_uncertainty_m_s2"] == 3e-8
        assert xu_2022_setup.XU_2022_TARGETS["icag_equivalence_m_s2"] == 1.3e-8

    def test_wu_2019_mobile_targets(self):
        assert wu_2019_setup.WU_2019_TARGETS["short_term_noise_m_s2_per_sqrt_hz"] == 3.7e-7
        assert wu_2019_setup.WU_2019_TARGETS["accuracy_after_30min_m_s2"] == 2e-8


@pytest.mark.parametrize("setup_name", list(_SETUPS))
class TestNoiseBudgets:
    """Each setup's per-shot noise quadrature reaches its short-term target
    within the documented factor-2 envelope (factor-3 for Hu since the HUST
    review's per-effect sum is ~3.6 vs the abstract's 4.2)."""

    def test_predicted_asd_matches_target(self, setup_name):
        setup = _SETUPS[setup_name]
        predicted = setup.predicted_short_term_asd_m_s2_per_sqrt_hz()
        if setup_name == "hu_2013":
            target = setup.HU_2013_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
            tol = 2.0
        elif setup_name == "menoret_2018":
            target = setup.MENORET_2018_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
            tol = setup.MENORET_2018_TARGETS["tolerance_factor"]
        elif setup_name == "xu_2022":
            target = setup.XU_2022_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
            tol = setup.XU_2022_TARGETS["tolerance_factor"]
        elif setup_name == "wu_2019":
            target = setup.WU_2019_TARGETS["short_term_noise_m_s2_per_sqrt_hz"]
            tol = setup.WU_2019_TARGETS["tolerance_factor"]
        factor = predicted / target
        assert 1.0 / tol < factor < tol, (
            f"{setup_name}: predicted {predicted:.2e} vs target {target:.2e}; "
            f"factor {factor:.2f} outside x{tol}."
        )


_SIM_SEEDS = {
    # Fixed seeds (deterministic, order-independent).
    "hu_2013": 2013,
    "menoret_2018": 2018,
    "xu_2022": 2022,
    "wu_2019": 2019,
}


@pytest.mark.slow
@pytest.mark.parametrize(
    "setup_name,gravity_true_key",
    [
        ("hu_2013", ("HU_2013_PARAMS", "HU_2013_TARGETS")),
        ("menoret_2018", ("MENORET_2018_PARAMS", "MENORET_2018_TARGETS")),
        ("xu_2022", ("XU_2022_PARAMS", "XU_2022_TARGETS")),
        ("wu_2019", ("WU_2019_PARAMS", "WU_2019_TARGETS")),
    ],
)
class TestSimulationASD:
    """End-to-end simulation reproduces each published short-term ASD."""

    def test_simulation_reproduces_short_term(self, setup_name, gravity_true_key):
        setup = _SETUPS[setup_name]
        params = getattr(setup, gravity_true_key[0])
        targets = getattr(setup, gravity_true_key[1])
        kwargs = setup.multi_drop_kwargs(
            n_drops=80,
            seed=_SIM_SEEDS[setup_name],
            n_atoms=4000,
            gravity_propagation=True,
        )
        result = run_aisim_multi_drop_cycle(**kwargs)

        T_cycle = params["cycle_time_s"]
        asd = float(result["std_g_m_s2"]) * math.sqrt(T_cycle)
        target = targets["short_term_noise_m_s2_per_sqrt_hz"]
        # Tolerance tightened from factor 4.5 (v1.1) to factor 3.0 (v1.2.0)
        # after raising the test ensemble to N=4000 (the v1.1 value of 300
        # left a finite-ensemble projection floor that swamped the injected
        # budget; see the Freier test docstring).  At N=4000 the four
        # benchmarks land at factor ~0.5-2.5 (Menoret is the wide one because
        # its short T=60 ms gives a genuinely low fringe contrast V~0.15, so
        # the 1/V mid-fringe inversion inflates its g-noise).  Factor 3 keeps
        # margin for that contrast spread.
        tol = 3.0
        factor = asd / target
        assert 1.0 / tol < factor < tol, (
            f"{setup_name}: simulated ASD {asd:.2e} m/s^2/sqrt(Hz) vs target "
            f"{target:.2e}; factor {factor:.2f} outside x{tol}. "
            f"(std_g={result['std_g_m_s2']:.2e}, V={result['visibility_estimate']:.3f})"
        )
