import numpy as np

from qgrav.metrics import (
    allan_deviation_overlapping,
    available_allan_backends,
    compute_error_statistics,
    compute_psd,
)


def test_psd_shapes_periodogram():
    fs = 100.0
    t = np.arange(0, 2.0, 1 / fs)
    x = np.sin(2 * np.pi * 5 * t)
    out = compute_psd(x, fs, method="periodogram")
    assert out["f_hz"].shape == out["psd"].shape
    assert len(out["f_hz"]) > 10


def test_psd_shapes_welch():
    fs = 100.0
    t = np.arange(0, 4.0, 1 / fs)
    x = np.sin(2 * np.pi * 5 * t)
    out = compute_psd(x, fs, method="welch", nperseg=128, noverlap=64)
    assert out["f_hz"].shape == out["psd"].shape
    assert len(out["f_hz"]) > 10


def test_allan_basic_custom_freq():
    fs = 100.0
    x = np.random.default_rng(0).normal(size=1000)
    taus = np.array([1 / fs, 2 / fs, 5 / fs, 10 / fs])
    out = allan_deviation_overlapping(x, fs, taus, backend="custom", data_type="freq")
    assert out["taus_s"].shape == out["adev"].shape
    assert np.isfinite(np.asarray(out["adev"])[0])


def test_allan_backends_match_freq():
    if "allantools" not in available_allan_backends():
        raise AssertionError("Vendored AllanTools backend is expected to be available.")
    fs = 100.0
    x = np.random.default_rng(1).normal(size=2000)
    taus = np.array([1 / fs, 2 / fs, 5 / fs, 10 / fs, 20 / fs])
    custom = allan_deviation_overlapping(x, fs, taus, backend="custom", data_type="freq")
    ref = allan_deviation_overlapping(x, fs, taus, backend="allantools", data_type="freq")
    np.testing.assert_allclose(
        np.asarray(custom["taus_s"]), np.asarray(ref["taus_s"]), rtol=0, atol=0
    )
    np.testing.assert_allclose(
        np.asarray(custom["adev"]), np.asarray(ref["adev"]), rtol=1e-12, atol=1e-12
    )


def test_allan_backends_match_phase():
    fs = 100.0
    x = np.cumsum(np.random.default_rng(2).normal(size=2000))
    taus = np.array([1 / fs, 2 / fs, 5 / fs, 10 / fs])
    custom = allan_deviation_overlapping(x, fs, taus, backend="custom", data_type="phase")
    ref = allan_deviation_overlapping(x, fs, taus, backend="allantools", data_type="phase")
    np.testing.assert_allclose(
        np.asarray(custom["taus_s"]), np.asarray(ref["taus_s"]), rtol=0, atol=0
    )
    np.testing.assert_allclose(
        np.asarray(custom["adev"]), np.asarray(ref["adev"]), rtol=1e-10, atol=1e-10
    )


def test_error_stats():
    y_true = np.array([0.0, 1.0, 2.0])
    y_hat = np.array([0.0, 1.1, 1.9])
    stats = compute_error_statistics(y_true, y_hat)
    assert stats["rmse"] >= 0.0
    assert stats["mae"] >= 0.0


def test_identify_noise_type_white_freq():
    """White frequency noise should have ADEV slope near -0.5."""
    rng = np.random.default_rng(42)
    x = rng.normal(size=10000)
    from qgrav.metrics.allan import allan_deviation_overlapping, identify_noise_type

    taus_req = np.logspace(0, 2, 20)
    result = allan_deviation_overlapping(x, 100.0, taus_req, backend="custom", data_type="freq")
    noise = identify_noise_type(np.asarray(result["taus_s"]), np.asarray(result["adev"]))
    assert -0.8 < noise["slope"] < -0.2
    assert noise["fit_r2"] > 0.5


def test_identify_noise_type_random_walk():
    """Random walk (cumulative sum of white noise) should have positive slope."""
    rng = np.random.default_rng(123)
    x = np.cumsum(rng.normal(size=5000))
    from qgrav.metrics.allan import allan_deviation_overlapping, identify_noise_type

    taus_req = np.logspace(0, 2, 15)
    result = allan_deviation_overlapping(x, 100.0, taus_req, backend="custom", data_type="freq")
    noise = identify_noise_type(np.asarray(result["taus_s"]), np.asarray(result["adev"]))
    assert noise["slope"] > 0.0


def test_identify_noise_type_insufficient_data():
    from qgrav.metrics.allan import identify_noise_type

    noise = identify_noise_type(np.array([1.0]), np.array([0.5]))
    assert noise["noise_type"] == "insufficient_data"


def test_allan_minimum_basic():
    taus = np.array([1, 2, 4, 8, 16, 32], dtype=float)
    adev = np.array([0.5, 0.3, 0.1, 0.05, 0.08, 0.2])
    from qgrav.metrics.allan import allan_minimum

    result = allan_minimum(taus, adev)
    assert result["min_adev"] == 0.05
    assert result["min_tau_s"] == 8.0
    assert result["min_index"] == 3


def test_match_taus_with_float_perturbation():
    from qgrav.pipeline._common import _match_taus

    t1 = np.array([1.0, 2.0, 4.0, 8.0])
    t2 = np.array([1.0 + 1e-14, 2.0 - 1e-14, 4.0, 8.0 + 1e-15])
    i1, i2 = _match_taus(t1, t2)
    assert len(i1) == 4
    assert len(i2) == 4
    np.testing.assert_array_equal(i1, [0, 1, 2, 3])
    np.testing.assert_array_equal(sorted(i2), [0, 1, 2, 3])


def test_match_taus_no_duplicate_targets():
    """Each taus2 element should be matched at most once."""
    from qgrav.pipeline._common import _match_taus

    t1 = np.array([1.0, 1.0 + 1e-15])  # two nearly identical source values
    t2 = np.array([1.0])  # one target
    i1, i2 = _match_taus(t1, t2)
    # Only one of t1[0] or t1[1] should match t2[0], not both
    assert len(i1) == 1
    assert len(i2) == 1
    assert i2[0] == 0


def test_match_taus_empty():
    from qgrav.pipeline._common import _match_taus

    i1, i2 = _match_taus(np.array([]), np.array([1.0]))
    assert len(i1) == 0
    i1, i2 = _match_taus(np.array([1.0]), np.array([]))
    assert len(i1) == 0
