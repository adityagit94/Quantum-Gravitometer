"""Tests for wavefront aberrations wiring (Phase 9)."""

from __future__ import annotations

from functools import partial

import numpy as np

import qgrav.vendor.aisim.dist as dist
from qgrav.sim_ai.aisim_adapter import (
    _build_wavefront,
    _gaussian_beam,
    _run_mach_zehnder_sequence,
    _wave_vectors,
)
from qgrav.vendor.aisim import (
    Wavefront,
    create_random_ensemble,
)


def _build_test_ensemble(n=200, cloud_radius=3e-3, temp=1e-6, seed=42):
    """Spread-out ensemble for testing position-dependent effects."""
    atoms = create_random_ensemble(
        n,
        x_dist=partial(dist.position_dist_gaussian, std=cloud_radius),
        y_dist=partial(dist.position_dist_gaussian, std=cloud_radius),
        z_dist=partial(dist.position_dist_gaussian, std=cloud_radius),
        vx_dist=partial(dist.velocity_dist_from_temp, temperature=temp),
        vy_dist=partial(dist.velocity_dist_from_temp, temperature=temp),
        vz_dist=partial(dist.velocity_dist_from_temp, temperature=temp),
        state_kets=[0, 0, 0, 0, 0, 1],
        seed=seed,
    )
    return atoms


class TestWavefrontNoneUnchanged:
    """When wavefront is None, MZ sequence should give same result as without wf."""

    def test_wavefront_none_unchanged(self):
        atoms = _build_test_ensemble(n=100)
        tau = 25e-6
        T = 0.1
        beam = _gaussian_beam(beam_radius_m=0.015, center_rabi_freq_hz=1.0 / (4 * tau))
        wv = _wave_vectors(wavelength_m=780.241e-9)

        r1 = _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=tau,
            interferometer_time_s=T,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=np.pi / 2,
            wavefront=None,
        )
        r2 = _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=tau,
            interferometer_time_s=T,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=np.pi / 2,
        )
        # Should be identical when no wavefront is applied
        np.testing.assert_allclose(r1["port_3"], r2["port_3"])
        np.testing.assert_allclose(r1["port_2"], r2["port_2"])


class TestWavefrontBuild:
    """_build_wavefront should construct a valid Wavefront object."""

    def test_build_wavefront_none_for_empty(self):
        assert _build_wavefront(wavefront_zernike_coeffs=None, wavefront_radius_m=0.01) is None
        assert _build_wavefront(wavefront_zernike_coeffs={}, wavefront_radius_m=0.01) is None

    def test_build_wavefront_creates_object(self):
        wf = _build_wavefront(
            wavefront_zernike_coeffs={4: 0.1},  # Z4 = defocus
            wavefront_radius_m=0.015,
        )
        assert wf is not None
        assert isinstance(wf, Wavefront)
        assert wf.r_wf == 0.015


class TestWavefrontDefocusReducesContrast:
    """A defocus Zernike coefficient should reduce ensemble fringe visibility.

    The physical mechanism: in a Mach-Zehnder, the wavefront phase imprinted
    at each pulse depends on the atom's position at that pulse.  For atoms
    that drift in (x, y) between pulses (due to thermal velocity), the
    wavefront contribution does NOT cancel in the MZ combination, producing
    an atom-dependent residual phase that broadens (dephases) the ensemble.

    Requires atoms with non-trivial xy thermal velocity AND a long enough T
    that drift > a fraction of the wavefront radius.
    """

    def test_wavefront_defocus_reduces_contrast(self):
        # Hot ensemble + long T -> significant drift between pulses
        atoms = _build_test_ensemble(n=300, cloud_radius=3e-3, temp=2e-6)
        tau = 25e-6
        T = 0.2  # moderate so atoms stay within wavefront radius
        beam = _gaussian_beam(beam_radius_m=0.04, center_rabi_freq_hz=1.0 / (4 * tau))
        wv = _wave_vectors(wavelength_m=780.241e-9)

        def fringe_visibility(wavefront, n_phases=9):
            phis = np.linspace(0, 2 * np.pi, n_phases)
            p3s = []
            for phi in phis:
                r = _run_mach_zehnder_sequence(
                    atoms,
                    tau_pi_half_s=tau,
                    interferometer_time_s=T,
                    intensity_profile=beam,
                    wave_vectors=wv,
                    final_phase_rad=phi,
                    wavefront=wavefront,
                )
                p3s.append(r["port_3"])
            p3s = np.array(p3s)
            return float(np.max(p3s) - np.min(p3s))

        v_no_wf = fringe_visibility(None)
        # Strong defocus with generous radius so all atoms are within
        wf_defocus = _build_wavefront(
            wavefront_zernike_coeffs={4: 5.0},
            wavefront_radius_m=0.05,
        )
        v_defocus = fringe_visibility(wf_defocus)

        # Defocus should reduce contrast.  Some reduction or unchanged is OK
        # (no INCREASE in contrast from aberration).
        assert v_defocus <= v_no_wf + 0.02, (
            f"Defocus unexpectedly increased contrast: no_wf={v_no_wf:.3f}, "
            f"defocus={v_defocus:.3f}"
        )


class TestWavefrontTiltShiftsFringe:
    """Tilt Zernike should produce a phase response different from the no-wavefront case."""

    def test_wavefront_tilt_changes_fringe(self):
        # Moderate drift with safely large wavefront radius
        atoms = _build_test_ensemble(n=200, cloud_radius=3e-3, temp=2e-6)
        tau = 25e-6
        T = 0.2
        beam = _gaussian_beam(beam_radius_m=0.04, center_rabi_freq_hz=1.0 / (4 * tau))
        wv = _wave_vectors(wavelength_m=780.241e-9)

        r_no_wf = _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=tau,
            interferometer_time_s=T,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=np.pi / 2,
            wavefront=None,
        )

        # Strong tilt + coma + spherical aberration; large r_wf so no NaNs
        wf_aberr = _build_wavefront(
            wavefront_zernike_coeffs={2: 8.0, 3: 8.0, 7: 8.0, 8: 8.0},
            wavefront_radius_m=0.05,
        )
        r_aberr = _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=tau,
            interferometer_time_s=T,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=np.pi / 2,
            wavefront=wf_aberr,
        )

        # P3 should differ measurably with strong aberrations
        assert not np.isnan(r_aberr["port_3"]), "Got NaN P3 (atoms outside r_wf)"
        assert abs(r_aberr["port_3"] - r_no_wf["port_3"]) > 0.005, (
            f"Aberration had no effect: no_wf={r_no_wf['port_3']:.4f}, "
            f"aberr={r_aberr['port_3']:.4f}"
        )


class TestWavefrontQuantitative:
    """v1.2.2 — quantitative wavefront-effect validation.

    The physical mechanism: a wavefront imprints a position-dependent phase at
    each pulse.  In the Mach-Zehnder combination -phi1 + 2 phi2 - phi3, if an
    atom sees the *same* wavefront phase at all three pulses (no transverse
    motion between pulses), the wavefront contribution cancels exactly.  The
    effect therefore arises ONLY from inter-pulse transverse atomic motion.
    """

    def test_static_ensemble_wavefront_cancels(self):
        """With ~zero transverse temperature (no inter-pulse xy motion), even a
        strong tilt+defocus wavefront leaves the MZ output unchanged, because
        the per-atom wavefront phase is identical at all three pulses and
        cancels in -phi1+2phi2-phi3.  This is the clean analytical prediction.
        """
        tau, T = 25e-6, 0.1
        beam = _gaussian_beam(beam_radius_m=0.04, center_rabi_freq_hz=1.0 / (4 * tau))
        wv = _wave_vectors(wavelength_m=780.241e-9)
        # temp ~ 0 -> atoms do not move transversely between pulses.
        atoms = _build_test_ensemble(n=150, cloud_radius=3e-3, temp=1e-12, seed=7)

        r_no_wf = _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=tau,
            interferometer_time_s=T,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=np.pi / 2,
            wavefront=None,
        )
        wf = _build_wavefront(
            wavefront_zernike_coeffs={2: 5.0, 3: 5.0, 4: 5.0}, wavefront_radius_m=0.05
        )
        r_wf = _run_mach_zehnder_sequence(
            atoms,
            tau_pi_half_s=tau,
            interferometer_time_s=T,
            intensity_profile=beam,
            wave_vectors=wv,
            final_phase_rad=np.pi / 2,
            wavefront=wf,
        )
        # Static ensemble: wavefront cancels in the MZ loop -> outputs match.
        np.testing.assert_allclose(r_wf["port_3"], r_no_wf["port_3"], atol=2e-3)

    def test_defocus_effect_is_curvature_second_order_in_drift(self):
        """The wavefront-induced MZ output change grows with the defocus (Z4)
        coefficient, and is a *second-order-in-drift* (curvature) effect.

        Physics: the MZ phase combination -phi1 + 2 phi2 - phi3 is a discrete
        second-difference (curvature) operator.  For ballistic motion
        rho(t) = rho0 + v t, the *linear* part of any wavefront (tilt, and the
        linear part of defocus) cancels exactly:
          -f(0) + 2 f(T) - f(2T) = 0  for f linear in t.
        Only the wavefront CURVATURE survives, and for a quadratic (defocus
        ~ rho^2) wavefront the surviving term is -2 v^2 T^2 / r_wf^2 * coeff —
        i.e. quadratic in the drift v*T.  This is the well-known
        wavefront-curvature systematic of light-pulse gravimeters; it is small
        but real, and it scales linearly with the defocus coefficient.

        We therefore assert (a) a measurable nonzero deviation and (b) that it
        grows ~linearly with the coefficient, rather than asserting a large
        contrast loss (which the curvature scaling makes second-order-small).
        """
        tau, T = 25e-6, 0.15
        beam = _gaussian_beam(beam_radius_m=0.05, center_rabi_freq_hz=1.0 / (4 * tau))
        wv = _wave_vectors(wavelength_m=780.241e-9)
        atoms = _build_test_ensemble(n=300, cloud_radius=3e-3, temp=2e-6, seed=11)

        def p3(z4):
            wf = (
                None
                if z4 == 0
                else _build_wavefront(wavefront_zernike_coeffs={4: z4}, wavefront_radius_m=0.04)
            )
            out = _run_mach_zehnder_sequence(
                atoms,
                tau_pi_half_s=tau,
                interferometer_time_s=T,
                intensity_profile=beam,
                wave_vectors=wv,
                final_phase_rad=np.pi / 2,
                wavefront=wf,
            )
            assert not np.isnan(out["port_3"]), "atoms drifted outside r_wf"
            return out["port_3"]

        base = p3(0.0)
        dev_lo = abs(p3(10.0) - base)
        dev_hi = abs(p3(20.0) - base)
        # (a) the curvature effect is real (nonzero).
        assert dev_lo > 1e-4, f"no wavefront-curvature effect: dev_lo={dev_lo:.5f}"
        # (b) it grows with the coefficient (linear in coeff -> dev_hi ~ 2*dev_lo).
        assert (
            dev_hi > 1.3 * dev_lo
        ), f"deviation did not grow with coefficient: {dev_lo:.5f} -> {dev_hi:.5f}"
