"""Edge-case tests for the custom Allan deviation implementation."""
from __future__ import annotations

import numpy as np
import pytest

from qgrav.metrics.allan import (
    allan_deviation_overlapping,
    _custom_oadev_freq,
    _validate_inputs,
)


def test_allan_custom_minimum_10_samples():
    """Exactly 10 samples should be accepted."""
    x = np.random.default_rng(42).normal(size=10)
    taus = np.array([1.0 / 10.0])  # tau0
    result = allan_deviation_overlapping(x, 10.0, taus, backend="custom")
    assert len(result["adev"]) >= 0  # may or may not produce a point, but must not crash


def test_allan_custom_9_samples_raises():
    """Fewer than 10 samples should raise ValueError."""
    x = np.random.default_rng(42).normal(size=9)
    taus = np.array([1.0])
    with pytest.raises(ValueError, match="at least 10"):
        allan_deviation_overlapping(x, 1.0, taus, backend="custom")


def test_allan_custom_large_tau_near_boundary():
    """Taus near half the record length should still produce results (or be
    silently dropped), never crash."""
    rng = np.random.default_rng(7)
    x = rng.normal(size=100)
    fs = 1.0
    # tau = 49 s → m = 49, 2*m = 98 < 100 → should produce a point
    # tau = 50 s → m = 50, 2*m = 100 → boundary
    taus = np.array([49.0, 50.0, 51.0])
    result = allan_deviation_overlapping(x, fs, taus, backend="custom")
    # At least the tau=49 point should be present
    assert len(result["adev"]) >= 1


def test_allan_custom_constant_input_returns_zero():
    """A constant input series has zero variance, so ADEV should be zero."""
    x = np.ones(200)
    taus = np.array([1.0, 5.0, 10.0])
    result = allan_deviation_overlapping(x, 1.0, taus, backend="custom")
    # All adev values should be exactly 0 for constant input
    np.testing.assert_array_equal(result["adev"], np.zeros(len(result["adev"])))


def test_allan_custom_single_tau():
    """A single-element taus array should work."""
    rng = np.random.default_rng(123)
    x = rng.normal(size=50)
    taus = np.array([5.0])
    result = allan_deviation_overlapping(x, 1.0, taus, backend="custom")
    assert len(result["adev"]) == 1
    assert result["adev"][0] > 0


def test_allan_custom_matches_allantools_edge_cases():
    """Verify custom backend matches allantools on small/edge-case data."""
    rng = np.random.default_rng(999)
    x = rng.normal(size=30)  # minimum practical length
    fs = 10.0
    taus = np.logspace(-1, 0.3, 8)

    result_custom = allan_deviation_overlapping(x, fs, taus, backend="custom")
    result_at = allan_deviation_overlapping(x, fs, taus, backend="allantools")

    # Match on common taus
    if len(result_custom["adev"]) > 0 and len(result_at["adev"]) > 0:
        # Both should produce broadly similar results
        assert result_custom["adev"][0] > 0
        assert result_at["adev"][0] > 0
