"""Local physics overrides for the vendored AISim package.

These classes implement the qgrav v1.0 physics extensions as *subclasses* of
the upstream AISim classes, rather than as in-place patches of the vendored
source.  Keeping them here means ``qgrav/vendor/aisim/*.py`` stays byte-for-byte
identical to a clean upstream ``aisim`` install, so re-vendoring a newer AISim
release does not require manually re-applying patches.  (See Phase 12 of
``docs/ROADMAP_V1_TO_V2.md`` and the test ``tests/test_vendor_aisim_unmodified.py``
which enforces the vendored files carry no ``[LOCAL PATCH]`` markers.)

Four extensions are provided:

1. :class:`GravityFreePropagator` — exact ballistic propagation under uniform
   gravity with an optional linear gradient (new propagator, no upstream
   equivalent).
2. :class:`ChirpedWavevectors` — adds a ``chirp_rate_rad_per_s2`` term to the
   Doppler shift so the Raman laser can track falling atoms.
3. :class:`IntegratedPhaseTwoLevelTransitionPropagator` — replaces the upstream
   ``exp(-i*delta*t0)`` imprint with the physically correct integrated laser
   phase ``-k_eff*z(t0) + 0.5*chirp*t0**2`` and adds an optional AC-Stark /
   light-shift term ``Omega_eff**2/(4*Delta)``.
4. :class:`IntegratedPhaseSpatialSuperpositionTransitionPropagator` — the
   multi-momentum-state (block-diagonal) version that routes its internal
   two-level matrix through the integrated-phase propagator above.

The physics is documented in ``docs/PHYSICS_REVIEW_PACKET.md`` and validated
against the literature in ``docs/research/RESEARCH_AISIM_PHYSICS.md`` and
``docs/research/RESEARCH_FINITE_TAU_FORMULAS.md``.
"""

from __future__ import annotations

import copy

import numpy as np

from qgrav.vendor.aisim.beam import Wavevectors
from qgrav.vendor.aisim.prop import (
    Propagator,
    SpatialSuperpositionTransitionPropagator,
    TwoLevelTransitionPropagator,
)


class GravityFreePropagator(Propagator):
    """Free propagation under uniform gravity with an optional linear gradient.

    Atoms follow exact ballistic trajectories::

        z(t+dt) = z + v_z*dt - 0.5*g*dt**2
        v_z(t+dt) = v_z - g*dt

    The quantum state is unchanged (identity matrix) — a uniform gravitational
    potential adds only a global phase, it does not mix internal states.

    Parameters
    ----------
    time_delta : float
        propagation time in seconds
    g_m_s2 : float
        gravitational acceleration in m/s^2 (positive = downward), default 9.81
    gravity_gradient_per_m : float
        vertical gravity gradient dg/dz in 1/s^2, default 0.0
    z_ref_m : float
        reference height for the gradient in m, default 0.0
    """

    def __init__(self, time_delta, g_m_s2=9.81, gravity_gradient_per_m=0.0, z_ref_m=0.0):
        super().__init__(time_delta)
        self.g_m_s2 = float(g_m_s2)
        self.gravity_gradient_per_m = float(gravity_gradient_per_m)
        self.z_ref_m = float(z_ref_m)

    def _local_g(self, z):
        """Local g including linear gradient: g(z) = g0 + gamma*(z - z_ref)."""
        return self.g_m_s2 + self.gravity_gradient_per_m * (z - self.z_ref_m)

    def _prop_matrix(self, atoms):
        """Identity matrix — no light-matter interaction during free fall."""
        n_levels = atoms.state_kets[0].shape[0]
        return np.repeat([np.eye(n_levels)], repeats=len(atoms), axis=0)

    def propagate(self, atoms):
        """Propagate an ensemble ballistically under gravity.

        Overrides the base class entirely (no half-step split) because the
        quantum matrix is the identity — only classical kinematics are needed.
        """
        atoms = copy.deepcopy(atoms)
        dt = self.time_delta
        g_local = self._local_g(atoms.position[:, 2])
        # Exact ballistic kinematics
        atoms.position[:, 2] += atoms.velocity[:, 2] * dt - 0.5 * g_local * dt**2
        atoms.position[:, 0] += atoms.velocity[:, 0] * dt
        atoms.position[:, 1] += atoms.velocity[:, 1] * dt
        atoms.velocity[:, 2] -= g_local * dt
        atoms.time += dt
        return atoms


class ChirpedWavevectors(Wavevectors):
    """Raman wave vectors with an optional linear frequency chirp.

    For a laser chirped at rate ``alpha = chirp_rate_rad_per_s2`` (rad/s^2),
    the two-photon detuning gains a term ``alpha * atoms.time``.  Setting
    ``alpha = -k_eff * g_chirp`` cancels the gravity-induced Doppler shift of
    an atom co-falling at ``g_chirp``.

    For ``chirp_rate_rad_per_s2 == 0`` this is identical to the upstream
    :class:`~qgrav.vendor.aisim.beam.Wavevectors`.
    """

    def __init__(self, k1=8055366, k2=-8055366, chirp_rate_rad_per_s2=0.0):
        super().__init__(k1=k1, k2=k2)
        self.chirp_rate_rad_per_s2 = float(chirp_rate_rad_per_s2)

    def doppler_shift(self, atoms):
        base = super().doppler_shift(atoms)
        if self.chirp_rate_rad_per_s2 != 0.0:
            return base + self.chirp_rate_rad_per_s2 * atoms.time
        return base


class IntegratedPhaseTwoLevelTransitionPropagator(TwoLevelTransitionPropagator):
    """Two-level Raman propagator using the integrated laser phase + AC Stark.

    Replaces the upstream off-diagonal imprint ``exp(-i*(delta*t0 + phase))``
    with ``exp(-i*(imprint_phase + phase))`` where

        imprint_phase(t0) = -k_eff * z(t0) + 0.5 * chirp * t0**2

    i.e. the time-integral of the (possibly chirped) detuning, rather than the
    instantaneous ``delta(t0) * t0`` product.  For atoms at z=0 with constant
    velocity and zero chirp this reduces exactly to the upstream behaviour.

    When ``single_photon_detuning_hz != 0`` an AC-Stark / light-shift term
    ``Omega_eff**2 / (4*Delta)`` (with ``Delta = 2*pi*single_photon_detuning_hz``)
    is added to the two-photon detuning; it is position-dependent through the
    Gaussian-beam ``Omega_eff(r)``.
    """

    def __init__(
        self,
        time_delta,
        intensity_profile,
        wave_vectors=None,
        wf=None,
        phase_scan=0,
        single_photon_detuning_hz=0.0,
        pulse_center_timing=False,
    ):
        super().__init__(
            time_delta,
            intensity_profile=intensity_profile,
            wave_vectors=wave_vectors,
            wf=wf,
            phase_scan=phase_scan,
        )
        self.single_photon_detuning_hz = float(single_photon_detuning_hz)
        # [v1.2] Chirp-term time convention for the imprinted laser phase.
        #
        # When True, the chirp term is evaluated at the pulse CENTRE
        # (atoms.time + time_delta/2); when False (default), at the pulse
        # START (atoms.time).
        #
        # Empirical finding (v1.2.0, docs/research/RESEARCH_FINITE_TAU*.md):
        # pulse-centre timing does NOT reduce the constant g-independent
        # calibration residual at g=g_chirp (it enlarges it, ~1.1 -> ~5.0 rad
        # for GAIN parameters).  The residual is a finite-pulse *discretisation*
        # artefact of evaluating a single rotation matrix over the whole pulse,
        # not a time/position asymmetry; it is gravity-independent and removed
        # exactly by `_calibrate_gravity_phase_offset`, so it does not bias the
        # measured g.  The flag is retained for reproducibility/experimentation
        # and for the sub-pulse-integration path (n_substeps) which is the
        # rigorous way to remove it.  Default False reproduces v1.1 behaviour.
        self.pulse_center_timing = bool(pulse_center_timing)

    def _prop_matrix(self, atoms):
        # effective Rabi frequency at the atoms' positions
        Omega_eff = self.intensity_profile.get_rabi_freq(atoms.position)
        if self.wf is None:
            phase = 0
        else:
            phase = self.wf.get_value(atoms.position)
        phase += self.phase_scan

        if self.wave_vectors is None:
            delta = 0
            imprint_phase = 0
        else:
            # two-photon detuning (-v*k_eff, plus chirp*t if ChirpedWavevectors)
            delta = self.wave_vectors.doppler_shift(atoms)
            # Integrated laser phase: phi(t0) = -k_eff*z(t0) + 0.5*chirp*t0**2.
            # Reduces to -k_eff*v*t0 = delta*t0 for z=0, constant v, zero chirp.
            k_eff = self.wave_vectors.k1 - self.wave_vectors.k2
            chirp = getattr(self.wave_vectors, "chirp_rate_rad_per_s2", 0.0)
            z_at_pulse = atoms.position[:, 2]
            # Evaluate the chirp at the pulse centre (default) so it is
            # consistent with z_at_pulse, which is already mid-pulse.
            if getattr(self, "pulse_center_timing", True):
                t_imprint = atoms.time + self.time_delta / 2.0
            else:
                t_imprint = atoms.time
            imprint_phase = -k_eff * z_at_pulse + 0.5 * chirp * t_imprint**2

        # AC Stark / light shift: position-dependent through Omega_eff(r).
        single_photon_detuning_hz = getattr(self, "single_photon_detuning_hz", 0.0)
        if single_photon_detuning_hz != 0.0:
            Delta_rad_s = 2.0 * np.pi * single_photon_detuning_hz
            delta = delta + Omega_eff**2 / (4.0 * Delta_rad_s)

        Omega_R = np.sqrt(Omega_eff**2 + delta**2)
        tau = self.time_delta

        sin_theta = Omega_eff / Omega_R
        cos_theta = -delta / Omega_R

        u_ee = np.cos(Omega_R * tau / 2) - 1j * cos_theta * np.sin(Omega_R * tau / 2)
        u_ee *= np.exp(-1j * delta * tau / 2)

        u_eg = np.exp(-1j * (imprint_phase + phase)) * -1j * sin_theta * np.sin(Omega_R * tau / 2)
        u_eg *= np.exp(-1j * delta * tau / 2)

        u_ge = np.exp(+1j * (imprint_phase + phase)) * -1j * sin_theta * np.sin(Omega_R * tau / 2)
        u_ge *= np.exp(1j * delta * tau / 2)

        u_gg = np.cos(Omega_R * tau / 2) + 1j * cos_theta * np.sin(Omega_R * tau / 2)
        u_gg *= np.exp(1j * delta * tau / 2)

        u = np.array([[u_ee, u_eg], [u_ge, u_gg]], dtype="complex")
        u = np.transpose(u, (2, 0, 1))
        return u


class IntegratedPhaseSpatialSuperpositionTransitionPropagator(
    SpatialSuperpositionTransitionPropagator,
    IntegratedPhaseTwoLevelTransitionPropagator,
):
    """Block-diagonal spatial-superposition propagator with integrated phase.

    The method-resolution order is

        this -> SpatialSuperposition -> IntegratedPhaseTwoLevel ->
        TwoLevelTransitionPropagator -> Propagator

    so that the top-level ``_prop_matrix`` is
    :meth:`SpatialSuperpositionTransitionPropagator._prop_matrix` (which builds
    the block-diagonal matrix), while the ``super()._prop_matrix`` call *inside*
    it resolves to
    :meth:`IntegratedPhaseTwoLevelTransitionPropagator._prop_matrix` (the
    integrated-phase + AC-Stark two-level matrix).
    """

    def __init__(
        self,
        time_delta,
        intensity_profile,
        n_pulses,
        n_pulse,
        wave_vectors=None,
        wf=None,
        phase_scan=0,
        single_photon_detuning_hz=0.0,
        pulse_center_timing=False,
    ):
        # Routes through SpatialSuperposition.__init__ (sets n_pulses/n_pulse)
        # which calls super().__init__ -> IntegratedPhaseTwoLevel.__init__.
        super().__init__(
            time_delta,
            intensity_profile=intensity_profile,
            n_pulses=n_pulses,
            n_pulse=n_pulse,
            wave_vectors=wave_vectors,
            wf=wf,
            phase_scan=phase_scan,
        )
        self.single_photon_detuning_hz = float(single_photon_detuning_hz)
        self.pulse_center_timing = bool(pulse_center_timing)
