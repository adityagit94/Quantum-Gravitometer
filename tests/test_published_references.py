from qgrav.validation import REFERENCES, PublishedReference, compare_to_reference
import pytest


def test_references_keys_exist():
    expected = {"freier_2016_sensitivity", "menoret_2018_accuracy", "sg_noise_floor", "mz_visibility"}
    assert expected == set(REFERENCES.keys())


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
    result = compare_to_reference("sg_noise_floor", 1e-11)
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
