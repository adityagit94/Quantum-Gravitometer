"""v1.2.1 — QuTiP independent cross-validation of the Raman dynamics.

These tests are gated on QuTiP being installed (``pytest.importorskip``) so the
core suite is unaffected when QuTiP is absent.  Install with ``pip install
.[qutip]`` to run them.

The point: qgrav's closed-form 2x2 Raman matrix vs QuTiP's numerical
Schrodinger integration — a genuinely independent code path. Agreement is
evidence the matrix is correct (partial mitigation of "no independent review").
"""
from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("qutip")

from qgrav.validation.qutip_crosscheck import (  # noqa: E402
    analytic_rabi_population,
    aisim_rabi_population,
    compare_rabi_grid,
    qutip_rabi_population,
    qutip_spontaneous_emission_loss,
)


class TestRabiAgreement:
    """qgrav matrix == QuTiP integrator == closed form."""

    def test_pi_pulse_full_transfer(self):
        # On resonance (delta=0), Omega_eff*tau = pi -> full transfer P_e = 1.
        omega = 2 * np.pi * 1e4
        tau = np.pi / omega
        assert aisim_rabi_population(omega, 0.0, tau) == pytest.approx(1.0, abs=1e-6)
        assert qutip_rabi_population(omega, 0.0, tau) == pytest.approx(1.0, abs=1e-5)

    def test_pi_half_pulse_half_transfer(self):
        omega = 2 * np.pi * 1e4
        tau = np.pi / (2 * omega)
        assert aisim_rabi_population(omega, 0.0, tau) == pytest.approx(0.5, abs=1e-6)
        assert qutip_rabi_population(omega, 0.0, tau) == pytest.approx(0.5, abs=1e-5)

    def test_grid_agreement(self):
        """Over a grid of (Omega, delta, tau), all three engines agree."""
        r = compare_rabi_grid()
        # Closed-form matrix is exact vs the analytic formula.
        assert r["aisim_vs_analytic"] < 1e-12
        # QuTiP's numerical integrator agrees with both to its ODE tolerance.
        assert r["aisim_vs_qutip"] < 1e-4
        assert r["qutip_vs_analytic"] < 1e-4

    def test_off_resonance_suppression(self):
        # Large detuning strongly suppresses transfer; both engines must agree.
        omega = 2 * np.pi * 1e4
        delta = 2 * np.pi * 5e4   # 5x the Rabi freq
        tau = np.pi / omega
        p_ai = aisim_rabi_population(omega, delta, tau)
        p_qt = qutip_rabi_population(omega, delta, tau)
        assert p_ai < 0.1               # strongly suppressed
        assert p_ai == pytest.approx(p_qt, abs=1e-4)


class TestSpontaneousEmissionCrosscheck:
    """QuTiP Lindblad mesolve gives an SE loss of the same order as the
    qgrav analytic formula."""

    def test_spontaneous_emission_order_of_magnitude(self):
        from qgrav.physics.noise_models import spontaneous_emission_loss_probability

        omega = 2 * np.pi * 15e3
        delta_hz = 1e9
        tau = 25e-6
        analytic = spontaneous_emission_loss_probability(
            rabi_freq_rad_s=omega, single_photon_detuning_hz=delta_hz,
            pulse_duration_s=tau,
        )
        qt_loss = qutip_spontaneous_emission_loss(
            omega_eff=omega, single_photon_detuning_hz=delta_hz, tau=tau,
        )
        # Both should be small (~1e-7) and within ~2 orders of magnitude of
        # each other (the two models use different adiabatic-elimination
        # scalings, so this is an order-of-magnitude cross-check, not exact).
        assert 0 < qt_loss < 1e-3
        assert 0 < analytic < 1e-3
        ratio = qt_loss / analytic
        assert 0.01 < ratio < 100.0
