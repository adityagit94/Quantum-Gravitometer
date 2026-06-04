"""Independent QuTiP cross-validation of the qgrav Raman two-level dynamics.

qgrav (via the patched AISim propagator) computes the single-pulse Raman
evolution from a **closed-form 2x2 matrix**.  QuTiP computes the *same* physics
by **numerically integrating the Schrodinger equation** (``sesolve``) — a
genuinely independent code path.  Agreement to ~1e-6 validates the closed-form
matrix; a bug in the matrix elements would show up as a mismatch.

QuTiP also lets us model spontaneous emission rigorously via a Lindblad
collapse operator (``mesolve``), giving an independent order-of-magnitude check
on :func:`qgrav.physics.noise_models.spontaneous_emission_loss_probability`.

QuTiP is an **optional** dependency.  Import this module only when QuTiP is
installed; the tests use ``pytest.importorskip("qutip")``.

Physics
-------
For a driven two-level system with effective Rabi frequency ``Omega_eff`` and
two-photon detuning ``delta`` (both rad/s), the excited-state population after
a pulse of duration ``tau`` starting from the ground state is the standard
Rabi result

    P_e(tau) = (Omega_eff^2 / Omega_R^2) * sin^2(Omega_R * tau / 2),
    Omega_R  = sqrt(Omega_eff^2 + delta^2).

Both qgrav's matrix and QuTiP's integrator must reproduce this.
"""
from __future__ import annotations

import numpy as np

from qgrav.vendor.aisim import AtomicEnsemble, IntensityProfile
from qgrav.sim_ai._aisim_overrides import (
    ChirpedWavevectors,
    IntegratedPhaseTwoLevelTransitionPropagator,
)


def analytic_rabi_population(omega_eff: float, delta: float, tau: float) -> float:
    """Closed-form P_e (the reference both engines must match)."""
    omega_r = np.hypot(omega_eff, delta)
    if omega_r == 0:
        return 0.0
    return float((omega_eff**2 / omega_r**2) * np.sin(omega_r * tau / 2.0) ** 2)


def aisim_rabi_population(omega_eff: float, delta: float, tau: float) -> float:
    """Excited-state population after one qgrav Raman pulse, from the ground state.

    The two-photon detuning is set via the atom's z-velocity
    (``delta = -v_z * k_eff``); ``omega_eff`` is set by a flat intensity profile
    at the beam centre.  z=0 so the imprint phase is pure (no effect on
    population).
    """
    k_eff = 1.0  # arbitrary; only the product v_z*k_eff matters for delta
    v_z = -delta / k_eff
    psv = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, v_z]], dtype=np.float64)
    # state_kets=[1, 0]: index 0 = ground, index 1 = excited (qgrav convention).
    atoms = AtomicEnsemble(psv, state_kets=[1, 0])
    # Flat intensity (huge 1/e^2 radius) so Omega_eff(r=0) = omega_eff exactly.
    beam = IntensityProfile(r_profile=1e6, center_rabi_freq=float(omega_eff))
    wv = ChirpedWavevectors(k1=k_eff / 2.0, k2=-k_eff / 2.0)  # k1 - k2 = k_eff
    prop = IntegratedPhaseTwoLevelTransitionPropagator(
        float(tau), intensity_profile=beam, wave_vectors=wv,
    )
    out = prop.propagate(atoms)
    return float(out.state_occupation(1)[0])


def qutip_rabi_population(omega_eff: float, delta: float, tau: float) -> float:
    """Excited-state population after one pulse, integrated by QuTiP sesolve."""
    import qutip as qt

    # Rotating-frame Hamiltonian: H = (delta/2) sigma_z + (Omega_eff/2) sigma_x.
    H = 0.5 * delta * qt.sigmaz() + 0.5 * omega_eff * qt.sigmax()
    # basis(2, 0) = ground; basis(2, 1) = excited.
    psi0 = qt.basis(2, 0)
    e_ops = [qt.basis(2, 1) * qt.basis(2, 1).dag()]  # |e><e| projector
    res = qt.sesolve(H, psi0, [0.0, float(tau)], e_ops=e_ops)
    return float(res.expect[0][-1])


def compare_rabi_grid(
    omega_effs=None, deltas=None, taus=None,
) -> dict[str, float]:
    """Compare qgrav vs QuTiP vs the closed form over a grid of (Omega, delta, tau).

    Returns the max abs differences ``aisim_vs_qutip``, ``aisim_vs_analytic``,
    ``qutip_vs_analytic``.
    """
    if omega_effs is None:
        omega_effs = 2 * np.pi * np.array([5e3, 1e4, 2e4])  # rad/s
    if deltas is None:
        deltas = 2 * np.pi * np.array([0.0, 2e3, -5e3, 1e4])  # rad/s
    if taus is None:
        taus = np.array([10e-6, 23e-6, 50e-6])  # s

    max_aq = max_aa = max_qa = 0.0
    for w in omega_effs:
        for d in deltas:
            for t in taus:
                p_ai = aisim_rabi_population(float(w), float(d), float(t))
                p_qt = qutip_rabi_population(float(w), float(d), float(t))
                p_an = analytic_rabi_population(float(w), float(d), float(t))
                max_aq = max(max_aq, abs(p_ai - p_qt))
                max_aa = max(max_aa, abs(p_ai - p_an))
                max_qa = max(max_qa, abs(p_qt - p_an))
    return {
        "aisim_vs_qutip": max_aq,
        "aisim_vs_analytic": max_aa,
        "qutip_vs_analytic": max_qa,
    }


def qutip_spontaneous_emission_loss(
    *, omega_eff: float, single_photon_detuning_hz: float,
    tau: float, excited_state_lifetime_s: float = 26.24e-9,
) -> float:
    """Spontaneous-emission loss over a pulse, via a 3-level Lindblad mesolve.

    A 3-level Hilbert space ``{|g>, |e>, |L>}`` is used: the Raman drive couples
    ``|g> <-> |e>`` at ``Omega_eff``, and the *intermediate-state admixture*
    decays irreversibly into a "lost" reservoir state ``|L>`` at the adiabatic
    rate ``Gamma * (Omega_eff / 2 Delta)^2``.  The returned value is the
    population in ``|L>`` after the pulse — the fraction lost to spontaneous
    emission.  This is an order-of-magnitude cross-check on qgrav's analytic
    ``spontaneous_emission_loss_probability`` (the two use slightly different
    adiabatic-elimination scalings, so exact agreement is not expected).
    """
    import qutip as qt

    delta_rad_s = 2.0 * np.pi * single_photon_detuning_hz
    gamma = 1.0 / excited_state_lifetime_s
    admixture = omega_eff / (2.0 * delta_rad_s)
    gamma_eff = gamma * admixture**2

    g, e, lost = qt.basis(3, 0), qt.basis(3, 1), qt.basis(3, 2)
    # Drive g<->e (the |L> state is dark to the drive).
    H = 0.5 * omega_eff * (g * e.dag() + e * g.dag())
    # Irreversible leak e -> L at the admixed scattering rate.
    c_ops = [np.sqrt(gamma_eff) * lost * e.dag()]
    psi0 = e  # start in the (admixed) excited state — worst case for SE loss
    p_lost = lost * lost.dag()
    res = qt.mesolve(H, psi0, np.linspace(0.0, float(tau), 50), c_ops=c_ops,
                     e_ops=[p_lost])
    return float(res.expect[0][-1])
