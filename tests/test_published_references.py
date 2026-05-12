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
