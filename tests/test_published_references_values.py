"""Regression tests for the published-reference values registry.

These tests guard against future edits silently changing benchmark numbers.
Each value is also annotated with the published unit conversion so anyone
reading the test can verify the value against the paper.

History:
  - v0.7  → v0.8: two values in this registry were corrected and renamed
    (see ``_LEGACY_KEYS`` in ``published_references.py``).
  - v1.0.0 → v1.0.1: ``hu_2013_short_term_noise`` was off by a factor of 10
    and ``menoret_2018_short_term_noise`` was 0.67x of the published value.
    Both were fixed in v1.0.1.  See ``_V1_0_0_VALUE_BUGS``.
  - v1.0.1 → v1.0.2: the Topic-13 audit found three unit-category errors
    (kasevich_chu_1991, bidel_2018_marine, sg_noise_floor) and two ambiguous
    entries (nlnm_low_freq, mz_visibility).  See ``_V1_0_1_VALUE_BUGS`` and
    ``docs/research/RESEARCH_REFERENCE_AUDIT.md``.
"""
from __future__ import annotations

import math
import pytest

from qgrav.validation.published_references import (
    REFERENCES,
    _V1_0_0_VALUE_BUGS,
    _V1_0_1_VALUE_BUGS,
    get_reference,
)


class TestFreier2016Values:
    """Freier 2016 — primary regression target (per project roadmap).

    Reference: Freier et al., J. Phys. Conf. Ser. 723, 012050 (2016).
    """

    def test_short_term_noise_value(self):
        """Freier 2016 short-term noise = 96 nm/s^2/sqrt(Hz) = 9.6e-8 m/s^2/sqrt(Hz)."""
        ref = REFERENCES["freier_2016_short_term_noise"]
        assert ref.value == 9.6e-8, (
            "Freier 2016 is the PRIMARY regression target. The published "
            "short-term noise is 96 nm/s^2/sqrt(Hz) = 9.6e-8 m/s^2/sqrt(Hz)."
        )
        assert ref.unit == "m/s^2/sqrt(Hz)"
        assert ref.year == 2016

    def test_long_term_stability_value(self):
        """Freier 2016 long-term stability = 0.5 nm/s^2 = 5e-10 m/s^2."""
        ref = REFERENCES["freier_2016_long_term_stability"]
        assert ref.value == 5e-10
        assert ref.unit == "m/s^2"

    def test_accuracy_value(self):
        """Freier 2016 absolute accuracy = 39 nm/s^2 = 3.9e-8 m/s^2."""
        ref = REFERENCES["freier_2016_accuracy"]
        assert ref.value == 3.9e-8


class TestHu2013Values:
    """Hu 2013 — lab-best-case sensitivity benchmark.

    Reference: Hu et al., Phys. Rev. A 88, 043610 (2013), §III.

    .. note::
       This value was incorrect in qgrav v1.0.0 (set to 4.2e-9, factor of 10
       too small).  Fixed in v1.0.1.
    """

    def test_short_term_noise_value_v1_0_1_corrected(self):
        """Hu 2013 short-term noise = 4.2 microGal/sqrt(Hz) = 4.2e-8 m/s^2/sqrt(Hz)."""
        ref = REFERENCES["hu_2013_short_term_noise"]
        assert ref.value == 4.2e-8, (
            f"Hu 2013 short-term noise must equal 4.2e-8 m/s^2/sqrt(Hz) "
            f"(= 4.2 microGal/sqrt(Hz)). Got {ref.value!r}. "
            f"NOT 4.2e-9 (that was the qgrav v1.0.0 bug)."
        )
        assert ref.unit == "m/s^2/sqrt(Hz)"

    def test_v1_0_0_bug_documented(self):
        """The v1.0.0 bug must remain documented in _V1_0_0_VALUE_BUGS."""
        assert "hu_2013_short_term_noise" in _V1_0_0_VALUE_BUGS
        old, new, reason = _V1_0_0_VALUE_BUGS["hu_2013_short_term_noise"]
        assert old == 4.2e-9
        assert new == 4.2e-8
        assert "factor of 10" in reason.lower()


class TestMenoret2018Values:
    """Ménoret 2018 — transportable real-world robustness benchmark.

    Reference: Ménoret et al., Sci. Rep. 8, 12300 (2018).

    .. note::
       The short-term value was 5e-7 in qgrav v1.0.0 but the paper's Larzac
       Allan-deviation trace shows 750 nm/s^2/sqrt(Hz). Fixed in v1.0.1.
    """

    def test_short_term_noise_value_v1_0_1_corrected(self):
        """Ménoret 2018 short-term noise = 750 nm/s^2/sqrt(Hz) = 7.5e-7 m/s^2/sqrt(Hz)."""
        ref = REFERENCES["menoret_2018_short_term_noise"]
        assert ref.value == 7.5e-7, (
            f"Menoret 2018 short-term noise must equal 7.5e-7 m/s^2/sqrt(Hz) "
            f"(= 750 nm/s^2/sqrt(Hz)). Got {ref.value!r}. "
            f"NOT 5e-7 (that was the qgrav v1.0.0 bug)."
        )

    def test_long_term_stability_value(self):
        """Ménoret 2018 long-term stability < 10 nm/s^2 = 1e-8 m/s^2 = 1 microGal."""
        ref = REFERENCES["menoret_2018_long_term_stability"]
        assert ref.value == 1e-8

    def test_v1_0_0_bug_documented(self):
        """The v1.0.0 short-term-noise mistake must remain documented."""
        assert "menoret_2018_short_term_noise" in _V1_0_0_VALUE_BUGS
        old, new, _reason = _V1_0_0_VALUE_BUGS["menoret_2018_short_term_noise"]
        assert old == 5e-7
        assert new == 7.5e-7


class TestUnitConversionSanityChecks:
    """Cross-check that each reference value matches its description in
    obvious units. Catches accidental key/value mix-ups in future edits."""

    @pytest.mark.parametrize("key,expected_value,human_unit", [
        # micro-Gal -> m/s^2/sqrt(Hz)
        ("hu_2013_short_term_noise",        4.2e-8, "4.2 microGal/sqrt(Hz)"),
        ("freier_2016_short_term_noise",    9.6e-8, "96 nm/s^2/sqrt(Hz)"),
        ("menoret_2018_short_term_noise",   7.5e-7, "750 nm/s^2/sqrt(Hz)"),
        # nm/s^2 long-term
        ("freier_2016_long_term_stability", 5e-10, "0.5 nm/s^2"),
        ("menoret_2018_long_term_stability", 1e-8, "1 microGal = 10 nm/s^2"),
        # Misc
        ("freier_2016_accuracy",            3.9e-8, "39 nm/s^2"),
        ("peters_2001_accuracy",            3e-8,   "3 microGal"),
        # v1.0.2 audit corrections (docs/research/RESEARCH_REFERENCE_AUDIT.md):
        ("bidel_2018_marine",               8e-6,   "0.8 mGal/sqrt(Hz) static sensitivity"),
        ("bidel_2018_marine_static_uncertainty", 1.7e-6, "0.17 mGal static uncertainty"),
        ("kasevich_chu_1991_first_demo",    3e-6,   "dimensionless delta_g/g at 1000 s"),
        ("nlnm_low_freq",                   4e-10,  "NLNM ASD minimum -187.5 dB"),
        ("sg_noise_floor",                  1.8e-9, "LSBB SG ASD floor at 1 mHz"),
        ("sg_detectability_nGal",           1e-11,  "1 nGal freq-domain detectability"),
        ("mz_visibility",                   0.5,    "idealised MZ maximum"),
    ])
    def test_value_matches_human_description(self, key, expected_value, human_unit):
        ref = REFERENCES[key]
        assert math.isclose(ref.value, expected_value, rel_tol=1e-12), (
            f"{key}: expected {expected_value!r} ({human_unit}); got {ref.value!r}"
        )


class TestRegistryStructure:
    """The registry itself must remain well-formed."""

    def test_all_required_fields_present(self):
        for key, ref in REFERENCES.items():
            assert ref.key == key, f"{key}: key field doesn't match dict key"
            assert ref.description, f"{key}: missing description"
            assert ref.unit, f"{key}: missing unit"
            assert ref.source, f"{key}: missing source"
            assert ref.year >= 1991, f"{key}: implausible year"
            assert 0 <= ref.tolerance_pct <= 200, f"{key}: weird tolerance"
            assert ref.doi, f"{key}: missing DOI"

    def test_count_matches_expected(self):
        # 12 entries as of v1.0.0/v1.0.1; v1.0.2 added two split-out keys
        # (bidel_2018_marine_static_uncertainty, sg_detectability_nGal) when
        # the audit separated mis-typed quantities -> 14. If you add one,
        # update this number AND add a parametrised row above.
        assert len(REFERENCES) == 14

    def test_get_reference_handles_legacy_keys(self):
        with pytest.warns(DeprecationWarning):
            ref = get_reference("freier_2016_sensitivity")
        assert ref.key == "freier_2016_short_term_noise"


class TestV102AuditCorrections:
    """Regression tests for the Topic-13 reference-value audit (v1.0.2).

    See docs/research/RESEARCH_REFERENCE_AUDIT.md.
    """

    def test_kasevich_chu_retyped_to_dimensionless(self):
        """3e-6 is a dimensionless delta_g/g at 1000 s (sodium), not an ASD."""
        ref = REFERENCES["kasevich_chu_1991_first_demo"]
        assert ref.value == 3e-6
        assert "dimensionless" in ref.unit.lower()
        assert "sqrt(hz)" not in ref.unit.lower()

    def test_bidel_sensitivity_corrected(self):
        """True static sensitivity = 0.8 mGal/sqrt(Hz) = 8e-6 m/s^2/sqrt(Hz)."""
        ref = REFERENCES["bidel_2018_marine"]
        assert ref.value == 8e-6
        assert ref.unit == "m/s^2/sqrt(Hz)"

    def test_bidel_static_uncertainty_separated(self):
        """The 0.17 mGal static uncertainty is now its own key (no /sqrt(Hz))."""
        ref = REFERENCES["bidel_2018_marine_static_uncertainty"]
        assert ref.value == 1.7e-6
        assert ref.unit == "m/s^2"

    def test_sg_noise_floor_corrected_to_asd(self):
        """True SG ASD floor ~1.8e-9 m/s^2/sqrt(Hz) (LSBB best site, 1 mHz)."""
        ref = REFERENCES["sg_noise_floor"]
        assert ref.value == 1.8e-9
        assert ref.unit == "m/s^2/sqrt(Hz)"

    def test_sg_detectability_separated(self):
        """The 1 nGal frequency-domain detectability is now its own key."""
        ref = REFERENCES["sg_detectability_nGal"]
        assert ref.value == 1e-11
        assert ref.unit == "m/s^2"  # NOT an ASD

    def test_nlnm_corrected_to_band_minimum(self):
        """NLNM ASD minimum ~4e-10 m/s^2/sqrt(Hz) (-187.5 dB)."""
        ref = REFERENCES["nlnm_low_freq"]
        assert ref.value == 4e-10

    def test_mz_visibility_resourced(self):
        """Value unchanged (0.5) but no longer attributed to Peters 2001."""
        ref = REFERENCES["mz_visibility"]
        assert ref.value == 0.5
        assert "peters" not in ref.description.lower()

    def test_all_v102_bugs_documented(self):
        """Every audited key must remain documented in _V1_0_1_VALUE_BUGS."""
        for key in ("kasevich_chu_1991_first_demo", "bidel_2018_marine",
                    "sg_noise_floor", "nlnm_low_freq", "mz_visibility"):
            assert key in _V1_0_1_VALUE_BUGS, f"{key} missing from audit log"
            old, new, unit_change, reason = _V1_0_1_VALUE_BUGS[key]
            assert reason, f"{key}: empty reason"
