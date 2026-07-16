"""Guard tests: the vendored source trees must stay upstream-clean (Phase 12).

The qgrav v1.0 physics extensions were originally applied as in-place patches
to ``src/qgrav/vendor/aisim/*.py``.  Phase 12 moved them into
``src/qgrav/sim_ai/_aisim_overrides.py`` as subclasses so the vendored files
stay diffable against a clean upstream ``aisim`` install (which makes
re-vendoring a newer release trivial).

The guard has four layers:

1. Checksum manifest — every vendored ``.py``/``.json`` file (aisim AND
   allantools) must match a pinned, newline-normalized sha256, so ANY in-place
   edit fails CI even though the vendor tree is excluded from ruff/black/mypy.
2. Marker/symbol scan — the physics files ``prop.py``/``beam.py`` must contain
   no ``[LOCAL PATCH]`` markers and none of the qgrav extension symbols.
3. Signature check — upstream ``Wavevectors.__init__`` keeps its exact
   upstream parameters.
4. Behavioural equivalence — the override subclasses must reduce to upstream
   behaviour when the extension parameters are off.

One sanctioned deviation from upstream exists and is pinned as-is by the
manifest: ``aisim/atoms.py`` carries a ``[LOCAL PATCH]`` replacing an assert
with ``ValueError`` so ensemble validation survives ``python -O``.  Anyone
re-vendoring AISim must re-apply that patch (and regenerate the manifest).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np

_VENDOR_ROOT = Path(__file__).resolve().parent.parent / "src" / "qgrav" / "vendor"
_VENDOR = _VENDOR_ROOT / "aisim"

# sha256 of every vendored source/data file, newline-normalized (CRLF -> LF)
# so the manifest is stable across git line-ending settings on Windows/Linux.
# After an INTENTIONAL re-vendor, regenerate by printing _current_manifest()
# (see the failure message of test_vendor_files_match_manifest).
_VENDOR_MANIFEST = {
    "__init__.py": "b229b92531f09a16e53f2b62341c4e4cf7b808c2dc01194f70dbf9bb71c958f3",
    "aisim/__init__.py": "eee23aec7350ca4f3f862c77cb97bf43cf2d614de2546813971b9885cf208d33",
    "aisim/atoms.py": "828846c882a3880bdf70c429b6b940cf7197fe88855c7bdae765ff2ae5248a0f",
    "aisim/beam.py": "9a03cd82d086af6ce6a6c0e28a9e046c8016ba0a905f33bc4e9b992d159bb749",
    "aisim/convert.py": "8abdbc5a6ce66a74eaedd8c34b55af58a98882707b3c0b10545d332d3bca7673",
    "aisim/det.py": "9b54964ab2e77abca3223d297aed8c8255b1635f9e8270920284db9dec057db5",
    "aisim/dist.py": "1ab3bf26e36039a41096a468d8e45e384d574da58730b9f60187b0aa10f92572",
    "aisim/prop.py": "9b569490471f1c7af1b9861f2afcc76eb7193371b6fd0b317b1a45a6bc8afe52",
    "aisim/zern.py": "d4e1a2c1c78cc9293e19c1af60106bdd4dbc33869a4559baa61ba888e06773ab",
    "allantools/__init__.py": "994a818e46abb023be93eafca6cee55ad9c875f3808626186687aa9d22cd0116",
    "allantools/allantools.py": "0f3a20a3c9f3118a4504de7c826ed23fd0a55455762f254cbe9ab26dcdb1de0a",
    "allantools/allantools_info.json": "cdab9e22ea85a8bb1aedbbc48da1c3bf4a424fd6ddbb8ea68ded3f48c08e9e8d",
    "allantools/ci.py": "04d274b0b09bf0ebad71c6162698696d99d6ff3a56edbe9f6aea694b012e9037",
    "allantools/dataset.py": "3ba581f3944345ae7f804a531d038ebb03a9e2ca1dc8e1fd9669860e6a37aed7",
    "allantools/mask.py": "0a8f3cedc848a46d2971c18be347c088d98a31a1abd12fa9c5eb1d83eb2cef74",
    "allantools/noise.py": "b283cfd64bc898ceb567f6be49fb9428c579a1173cee635869229274268ad24b",
    "allantools/noise_kasdin.py": "a905ddda2ff022c37a4e5f5f70674c2905db8da8edf8562180ea0b843d9c379f",
    "allantools/plot.py": "e0a48463fd7abb1a1d1a68ca0210ba2e74ae5ce5dda91863cb02ecc979085e14",
    "allantools/realtime.py": "7bff993159029de954b52565f3d486026008315e1b9e081359c97b570d961a4b",
}


def _normalized_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _current_manifest() -> dict[str, str]:
    return {
        p.relative_to(_VENDOR_ROOT).as_posix(): _normalized_sha256(p)
        for p in sorted(_VENDOR_ROOT.rglob("*"))
        if p.suffix in {".py", ".json"} and "__pycache__" not in p.parts
    }


class TestVendorTreeChecksums:
    """Every vendored file must match the pinned checksum manifest."""

    def test_no_missing_or_unexpected_vendor_files(self):
        found = set(_current_manifest())
        pinned = set(_VENDOR_MANIFEST)
        assert found == pinned, (
            f"vendored file set changed. missing={sorted(pinned - found)} "
            f"unexpected={sorted(found - pinned)}. If this re-vendor is "
            "intentional, regenerate _VENDOR_MANIFEST via _current_manifest()."
        )

    def test_vendor_files_match_manifest(self):
        current = _current_manifest()
        mismatched = sorted(
            rel for rel, digest in _VENDOR_MANIFEST.items() if current.get(rel) != digest
        )
        assert not mismatched, (
            f"vendored files edited in place: {mismatched}. Never patch "
            "src/qgrav/vendor/ directly — extend via subclasses in "
            "qgrav/sim_ai/_aisim_overrides.py (see CONTRIBUTING.md). If this "
            "is an intentional re-vendor, regenerate _VENDOR_MANIFEST via "
            "_current_manifest() and document the upstream version in "
            "src/qgrav/vendor/ATTRIBUTION.md."
        )

    def test_atoms_local_patch_is_still_present(self):
        """The one sanctioned patch (assert -> ValueError for `python -O`
        safety) must survive re-vendoring; see the module docstring."""
        text = (_VENDOR / "atoms.py").read_text(encoding="utf-8")
        assert "[LOCAL PATCH]" in text


class TestVendorFilesHaveNoLocalPatches:
    """The vendored physics files must not contain '[LOCAL PATCH]' markers."""

    def test_prop_has_no_local_patch(self):
        text = (_VENDOR / "prop.py").read_text(encoding="utf-8")
        assert "[LOCAL PATCH]" not in text, (
            "vendor/aisim/prop.py contains a local patch. Move the extension "
            "into qgrav/sim_ai/_aisim_overrides.py (see CONTRIBUTING.md)."
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
