import warnings

import pytest

from qgrav.validation import REFERENCES, PublishedReference, compare_to_reference


def test_references_keys_exist():
    # v0.8: registry expanded to cover GAIN, AQG, Wuhan 10 m, Stanford,
    # Kasevich-Chu 1991, Bidel 2018 marine, NLNM, plus the v0.7 retained
    # entries. The exact set may grow; check the core members.
    core_v08 = {
        "freier_2016_short_term_noise",
        "freier_2016_accuracy",
        "freier_2016_long_term_stability",
        "menoret_2018_short_term_noise",
        "menoret_2018_long_term_stability",
        "hu_2013_short_term_noise",
        "peters_2001_accuracy",
        "kasevich_chu_1991_first_demo",
        "bidel_2018_marine",
        "nlnm_low_freq",
        "sg_noise_floor",
        "mz_visibility",
    }
    assert core_v08 <= set(REFERENCES.keys())


def test_legacy_keys_emit_deprecation_warning():
    """v0.7 keys still work but issue a DeprecationWarning."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = compare_to_reference("freier_2016_sensitivity", 9.6e-8)
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
    # The legacy key should resolve to the corrected entry.
    assert result["key"] == "freier_2016_short_term_noise"
    assert result["reference_value"] == 9.6e-8


def test_corrected_freier_short_term_noise_value():
    """Regression: v0.7 stored 5e-8; the true value is 9.6e-8 m/s^2/sqrt(Hz)."""
    assert REFERENCES["freier_2016_short_term_noise"].value == 9.6e-8


def test_all_references_are_frozen_dataclass():
    for ref in REFERENCES.values():
        assert isinstance(ref, PublishedReference)
        with pytest.raises(AttributeError):
            ref.value = 999  # type: ignore[misc]


def test_compare_within_tolerance():
    result = compare_to_reference("mz_visibility", 0.5)
    assert result["within_tolerance"] is True
    assert result["deviation_pct"] == 0.0


def test_compare_outside_tolerance():
    result = compare_to_reference("mz_visibility", 5.0)
    assert result["within_tolerance"] is False
    assert result["deviation_pct"] > 100.0


def test_compare_unknown_key():
    with pytest.raises(KeyError):
        compare_to_reference("nonexistent", 1.0)


def test_compare_result_keys():
    # v1.0.2: sg_noise_floor corrected to 1.8e-9 m/s^2/sqrt(Hz); use a value
    # in-band so the result dict is populated normally.
    result = compare_to_reference("sg_noise_floor", 1.8e-9)
    for k in ("key", "measured", "reference_value", "unit", "source", "within_tolerance", "deviation_pct", "tolerance_pct"):
        assert k in result


def test_contains_zero_value_reference():
    """When reference value is 0, the percentage band collapses. Verify abs_tol fallback."""
    ref = PublishedReference(
        key="zero_ref",
        description="Test zero-valued reference",
        value=0.0,
        unit="m/s^2",
        source="test",
        year=2024,
        tolerance_pct=10.0,
    )
    # Exact zero should be within tolerance
    assert ref.contains(0.0) is True
    # Tiny value within default abs_tol should be within tolerance
    assert ref.contains(1e-16) is True
    # Larger value should be outside tolerance
    assert ref.contains(1.0) is False
    # Custom abs_tol
    assert ref.contains(0.5, abs_tol=1.0) is True
    assert ref.contains(1.5, abs_tol=1.0) is False


def test_all_references_have_doi():
    """Every published reference should have a non-empty DOI."""
    for key, ref in REFERENCES.items():
        assert ref.doi, f"Reference {key!r} is missing a DOI"
        assert ref.doi.startswith("10."), f"Reference {key!r} DOI does not start with '10.': {ref.doi}"


def test_doi_field_exists_on_dataclass():
    """Verify doi is a proper field on the frozen dataclass."""
    ref = PublishedReference(
        key="test", description="test", value=1.0, unit="m", source="test", year=2024, doi="10.1234/test"
    )
    assert ref.doi == "10.1234/test"
    # Default doi should be empty string
    ref2 = PublishedReference(
        key="test2", description="test", value=1.0, unit="m", source="test", year=2024
    )
    assert ref2.doi == ""
