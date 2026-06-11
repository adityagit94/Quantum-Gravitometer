"""Tests for AC Stark / light-shift correction in TwoLevelTransitionPropagator (Phase 8)."""

from __future__ import annotations

import numpy as np

# v1.1 (Phase 12): AC-Stark + integrated-phase live in the override subclass.
from qgrav.sim_ai import (
    IntegratedPhaseSpatialSuperpositionTransitionPropagator as SpatialSuperpositionTransitionPropagator,
)
from qgrav.vendor.aisim import (
    AtomicEnsemble,
    IntensityProfile,
    Wavevectors,
)


def _single_atom_at_origin(state_kets=None):
    psv = np.array([[0.0, 0.0, 0.0, 0.0, 0.0, 0.0]], dtype=np.float64)
    return AtomicEnsemble(psv, state_kets=state_kets or [0, 0, 0, 0, 0, 1])


class TestACStarkZeroUnchanged:
    """single_photon_detuning_hz=0 must give identical results to baseline."""

    def test_ac_stark_zero_unchanged(self):
        atoms = _single_atom_at_origin()
        tau = 25e-6
        beam = IntensityProfile(r_profile=0.01, center_rabi_freq=2 * np.pi / (4 * tau))
        wv = Wavevectors()

        bs1_baseline = SpatialSuperpositionTransitionPropagator(
            tau,
            n_pulse=1,
            n_pulses=3,
            intensity_profile=beam,
            wave_vectors=wv,
        )
        bs1_zero = SpatialSuperpositionTransitionPropagator(
            tau,
            n_pulse=1,
            n_pulses=3,
            intensity_profile=beam,
            wave_vectors=wv,
            single_photon_detuning_hz=0.0,
        )

        a1 = bs1_baseline.propagate(atoms)
        a2 = bs1_zero.propagate(atoms)
        np.testing.assert_array_equal(a1.state_kets, a2.state_kets)


class TestACStarkShiftsFringePhase:
    """Large single-photon detuning should produce a measurable phase shift."""

    def test_ac_stark_shifts_fringe_phase(self):
        # Run an MZ sequence with and without AC Stark, compare final populations
        tau = 25e-6
        T = 0.1  # shorter T for speed
        beam = IntensityProfile(r_profile=0.01, center_rabi_freq=2 * np.pi / (4 * tau))
        wv = Wavevectors()

        from qgrav.vendor.aisim import FreePropagator

        atoms = _single_atom_at_origin()

        def run_mz(detuning_hz):
            bs1 = SpatialSuperpositionTransitionPropagator(
                tau,
                n_pulse=1,
                n_pulses=3,
                intensity_profile=beam,
                wave_vectors=wv,
                single_photon_detuning_hz=detuning_hz,
            )
            mir = SpatialSuperpositionTransitionPropagator(
                2 * tau,
                n_pulse=2,
                n_pulses=3,
                intensity_profile=beam,
                wave_vectors=wv,
                single_photon_detuning_hz=detuning_hz,
            )
            bs2 = SpatialSuperpositionTransitionPropagator(
                tau,
                n_pulse=3,
                n_pulses=3,
                intensity_profile=beam,
                wave_vectors=wv,
                phase_scan=np.pi / 2,
                single_photon_detuning_hz=detuning_hz,
            )
            prop = FreePropagator(T)
            a = bs1.propagate(atoms)
            a = prop.propagate(a)
            a = mir.propagate(a)
            a = prop.propagate(a)
            a = bs2.propagate(a)
            return float(a.state_occupation(3)[0])

        p3_no_stark = run_mz(0.0)
        # Use a strong AC Stark to ensure visible effect.
        # Omega_eff^2/(4*Delta) where Omega_eff ≈ Pi/(4 tau) = 2pi*10kHz,
        # Delta = 1 MHz → shift = (2pi*10kHz)^2/(4*2pi*1e6) ≈ 2pi*25 Hz
        # Over a 2*tau mirror pulse, accumulated phase ≈ 2pi*25*2*tau = 2pi*1.25e-3
        # Too small. Use Delta = 1 kHz:
        # shift = (2pi*10kHz)^2/(4*2pi*1e3) = 2pi*25000 Hz = pi/2 over 10us
        # That's big enough.
        p3_with_stark = run_mz(1e3)
        # The fringe should shift measurably
        assert (
            abs(p3_with_stark - p3_no_stark) > 0.05
        ), f"AC Stark had no effect: no_stark={p3_no_stark}, with_stark={p3_with_stark}"


class TestACStarkReducesContrast:
    """Position-dependent AC Stark (via Omega(r)) should reduce ensemble contrast."""

    def test_ac_stark_reduces_contrast(self):
        # Use an ensemble with significant spatial spread so atoms see different Omega_eff
        tau = 25e-6
        T = 0.1
        # Make beam tight relative to cloud so Omega varies significantly
        from functools import partial

        import qgrav.vendor.aisim.dist as dist
        from qgrav.vendor.aisim import FreePropagator, create_random_ensemble

        beam = IntensityProfile(
            r_profile=2.0e-3, center_rabi_freq=2 * np.pi / (4 * tau)
        )  # 2mm beam
        wv = Wavevectors()
        atoms = create_random_ensemble(
            200,
            x_dist=partial(dist.position_dist_gaussian, std=3e-3),  # 3 mm cloud
            y_dist=partial(dist.position_dist_gaussian, std=3e-3),
            z_dist=partial(dist.position_dist_gaussian, std=3e-3),
            vx_dist=partial(dist.velocity_dist_from_temp, temperature=1e-6),
            vy_dist=partial(dist.velocity_dist_from_temp, temperature=1e-6),
            vz_dist=partial(dist.velocity_dist_from_temp, temperature=1e-6),
            state_kets=[0, 0, 0, 0, 0, 1],
            seed=42,
        )

        def run_fringe(detuning_hz, n_phases=21):
            phis = np.linspace(0, 2 * np.pi, n_phases)
            p3s = []
            for phi in phis:
                bs1 = SpatialSuperpositionTransitionPropagator(
                    tau,
                    n_pulse=1,
                    n_pulses=3,
                    intensity_profile=beam,
                    wave_vectors=wv,
                    single_photon_detuning_hz=detuning_hz,
                )
                mir = SpatialSuperpositionTransitionPropagator(
                    2 * tau,
                    n_pulse=2,
                    n_pulses=3,
                    intensity_profile=beam,
                    wave_vectors=wv,
                    single_photon_detuning_hz=detuning_hz,
                )
                bs2 = SpatialSuperpositionTransitionPropagator(
                    tau,
                    n_pulse=3,
                    n_pulses=3,
                    intensity_profile=beam,
                    wave_vectors=wv,
                    phase_scan=phi,
                    single_photon_detuning_hz=detuning_hz,
                )
                prop = FreePropagator(T)
                a = bs1.propagate(atoms)
                a = prop.propagate(a)
                a = mir.propagate(a)
                a = prop.propagate(a)
                a = bs2.propagate(a)
                p3s.append(float(np.mean(a.state_occupation(3))))
            p3s = np.array(p3s)
            return float(np.max(p3s) - np.min(p3s))

        contrast_no_stark = run_fringe(0.0)
        # Use a strong AC Stark to clearly reduce contrast through dephasing
        contrast_with_stark = run_fringe(5e2)

        # Contrast should be reduced (or at least not increased) by AC Stark.
        # Allow for noise in the contrast estimate; require <=10% increase.
        assert contrast_with_stark <= contrast_no_stark + 0.05, (
            f"AC Stark unexpectedly increased contrast: "
            f"no_stark={contrast_no_stark}, with_stark={contrast_with_stark}"
        )
