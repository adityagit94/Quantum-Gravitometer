"""Guard tests: the vendored AISim source must stay upstream-clean (Phase 12).

The qgrav v1.0 physics extensions were originally applied as in-place patches
to ``src/qgrav/vendor/aisim/*.py``.  Phase 12 moved them into
``src/qgrav/sim_ai/_aisim_overrides.py`` as subclasses so the vendored files
remain byte-for-byte identical to a clean upstream ``aisim`` install (which
makes re-vendoring a newer release trivial).

These tests fail if a future edit re-introduces a local patch into the
vendored package, or if the override subclasses go missing.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

_VENDOR = Path(__file__).resolve().parent.parent / "src" / "qgrav" / "vendor" / "aisim"


class TestVendorFilesHaveNoLocalPatches:
    """The vendored physics files must not contain '[LOCAL PATCH]' markers."""

    def test_prop_has_no_local_patch(self):
        text = (_VENDOR / "prop.py").read_text(encoding="utf-8")
        assert "[LOCAL PATCH]" not in text, (
            "vendor/aisim/prop.py contains a local patch. Move the extension "
            "into qgrav/sim_ai/_aisim_overrides.py (see Phase 12 of "
            "docs/ROADMAP_V1_TO_V2.md)."
        )

    def test_beam_has_no_local_patch(self):
        text = (_VENDOR / "beam.py").read_text(encoding="utf-8")
        assert "[LOCAL PATCH]" not in text, (
            "vendor/aisim/beam.py contains a local patch. Move the extension "
            "into qgrav/sim_ai/_aisim_overrides.py."
        )

    def test_vendor_prop_has_no_gravity_free_propagator(self):
        """GravityFreePropagator is a qgrav extension; it must NOT be in vendor."""
        text = (_VENDOR / "prop.py").read_text(encoding="utf-8")
        assert "class GravityFreePropagator" not in text

    def test_vendor_wavevectors_has_no_chirp(self):
        """The chirp parameter is a qgrav extension; not in vendored beam.py."""
        text = (_VENDOR / "beam.py").read_text(encoding="utf-8")
        assert "chirp_rate_rad_per_s2" not in text

    def test_vendor_twolevel_has_no_single_photon_detuning(self):
        """AC-Stark single_photon_detuning_hz is a qgrav extension."""
        text = (_VENDOR / "prop.py").read_text(encoding="utf-8")
        assert "single_photon_detuning_hz" not in text


class TestUpstreamWavevectorsRejectsChirp:
    """The clean vendored Wavevectors must not accept a chirp kwarg."""

    def test_upstream_wavevectors_signature(self):
        import inspect

        from qgrav.vendor.aisim import Wavevectors

        params = inspect.signature(Wavevectors.__init__).parameters
        assert "chirp_rate_rad_per_s2" not in params
        assert set(params) == {"self", "k1", "k2"}


class TestOverridesEquivalentToUpstreamAtZeroExtension:
    """The override subclasses must reduce to upstream behaviour when the
    extension parameters are off (chirp=0, single_photon_detuning=0,
    atoms at z=0)."""

    def test_chirped_wavevectors_zero_matches_upstream(self):
        from qgrav.sim_ai import ChirpedWavevectors
        from qgrav.vendor.aisim import AtomicEnsemble, Wavevectors

        psv = np.zeros((4, 6), dtype=np.float64)
        psv[:, 5] = np.linspace(-0.1, 0.1, 4)
        atoms = AtomicEnsemble(psv, state_kets=[1, 0], time=0.2)
        up = Wavevectors().doppler_shift(atoms)
        ov = ChirpedWavevectors(chirp_rate_rad_per_s2=0.0).doppler_shift(atoms)
        np.testing.assert_array_equal(up, ov)

    def test_integrated_twolevel_matches_upstream_at_z0(self):
        """For atoms at z=0 with constant velocity and zero chirp, the
        integrated-phase 2-level matrix equals the upstream one."""
        from qgrav.sim_ai import (
            ChirpedWavevectors,
            IntegratedPhaseTwoLevelTransitionPropagator,
        )
        from qgrav.vendor.aisim import (
            AtomicEnsemble,
            IntensityProfile,
            TwoLevelTransitionPropagator,
            Wavevectors,
        )

        tau = 25e-6
        beam = IntensityProfile(r_profile=0.01, center_rabi_freq=2 * np.pi / (4 * tau))
        # atoms at z=0 (so -k_eff*z(t0) == delta*t0 for constant velocity)
        psv = np.zeros((3, 6), dtype=np.float64)
        psv[:, 5] = np.array([-0.01, 0.0, 0.01])  # vz spread
        atoms = AtomicEnsemble(psv, state_kets=[1, 0], time=0.0)

        up = TwoLevelTransitionPropagator(
            tau, intensity_profile=beam, wave_vectors=Wavevectors()
        ).propagate(atoms)
        ov = IntegratedPhaseTwoLevelTransitionPropagator(
            tau,
            intensity_profile=beam,
            wave_vectors=ChirpedWavevectors(),
        ).propagate(atoms)
        np.testing.assert_allclose(
            np.abs(np.asarray(up.state_kets)),
            np.abs(np.asarray(ov.state_kets)),
            atol=1e-12,
        )
