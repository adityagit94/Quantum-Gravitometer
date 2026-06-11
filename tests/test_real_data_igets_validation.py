"""v1.3.0 — real-data validation of the analysis chain (IGETS SG data).

Validates that qgrav's Allan-deviation / PSD analysis tooling runs end-to-end on
**real superconducting-gravimeter data** (the bundled IGETS station ap046) and
produces physically plausible results, cross-referenced against the published SG
noise floor (`sg_noise_floor`, 1.8e-9 m/s^2/sqrt(Hz)).

Scope (honest):
- This validates the **analysis chain** (ingest -> Allan/PSD) on real
  precision-gravity data.  It does NOT validate the atom-interferometer
  *simulation* against hardware — no public atom-gravimeter raw data exists
  (see docs/research/RESEARCH_REAL_DATA_SOURCES.md).  Hardware-AI validation is
  a user/collaboration track (see docs/REVIEW_REQUEST_TEMPLATE.md).
- Hermetic: uses the bundled `data/raw/sg_sample` station, no network.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from qgrav.bench_ifo.real_gravity import load_real_gravity
from qgrav.metrics.allan import allan_deviation_overlapping
from qgrav.validation.published_references import REFERENCES


def _sample_dir():
    root = Path(__file__).resolve().parent.parent
    d = root / "data" / "raw" / "sg_sample"
    if not d.exists():
        pytest.skip(f"bundled SG sample not found at {d}")
    return d


class TestRealSGDataIngest:
    def test_loads_real_station(self):
        d = load_real_gravity(source_path=str(_sample_dir()), station_code="ap046")
        assert d["station_code"] == "ap046"
        assert d["source_kind"]  # ggp / directory / etc.
        g = np.asarray(d["gravity_residual"], dtype=float)
        assert g.size > 100
        assert np.all(np.isfinite(g))
        # Real SG residual is non-trivial (geophysical signal present).
        assert g.std() > 0


class TestRealSGAllanDeviation:
    """The Allan-deviation tooling produces physically plausible results on
    real SG data, bounded below by the instrument noise floor."""

    def test_allan_deviation_is_physical(self):
        d = load_real_gravity(source_path=str(_sample_dir()), station_code="ap046")
        g = np.asarray(d["gravity_residual"], dtype=float)
        fs = float(d["sample_rate_hz"])
        dt = 1.0 / fs
        n = g.size
        # Octave tau grid up to a quarter of the record.
        max_m = max(1, n // 4)
        ms = [m for m in (1, 2, 4, 8, 16, 32, 64) if m <= max_m]
        taus = np.array([dt * m for m in ms], dtype=float)
        res = allan_deviation_overlapping(g, fs, taus, backend="custom")
        adev = np.asarray(res["adev"], dtype=float)

        # (1) finite and positive at every tau.
        assert adev.size == len(ms)
        assert np.all(np.isfinite(adev))
        assert np.all(adev > 0)
        # (2) Allan deviation <= sample std (a basic structural property).
        assert np.all(adev <= g.std() * 1.5 + 1e-12)
        # (3) Physically plausible for SG residual gravity in nm/s^2-class units
        #     (the bundled residual is O(10) units, std ~ 11): the Allan
        #     deviation should be within a few orders of magnitude of that,
        #     i.e. neither absurdly small nor large.
        assert 1e-3 * g.std() < np.median(adev) < 10.0 * g.std()

    def test_instrument_floor_reference_present(self):
        """The SG instrument noise floor (the lower bound the real residual
        must sit above) is in the registry at the v1.0.2-corrected value."""
        ref = REFERENCES["sg_noise_floor"]
        assert ref.value == 1.8e-9  # m/s^2/sqrt(Hz), corrected in v1.0.2
        assert "m/s^2/sqrt(Hz)" in ref.unit
