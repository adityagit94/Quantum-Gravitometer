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
    np.testing.assert_allclose(np.asarray(custom["taus_s"]), np.asarray(ref["taus_s"]), rtol=0, atol=0)
    np.testing.assert_allclose(np.asarray(custom["adev"]), np.asarray(ref["adev"]), rtol=1e-12, atol=1e-12)


def test_allan_backends_match_phase():
    fs = 100.0
    x = np.cumsum(np.random.default_rng(2).normal(size=2000))
    taus = np.array([1 / fs, 2 / fs, 5 / fs, 10 / fs])
    custom = allan_deviation_overlapping(x, fs, taus, backend="custom", data_type="phase")
    ref = allan_deviation_overlapping(x, fs, taus, backend="allantools", data_type="phase")
    np.testing.assert_allclose(np.asarray(custom["taus_s"]), np.asarray(ref["taus_s"]), rtol=0, atol=0)
    np.testing.assert_allclose(np.asarray(custom["adev"]), np.asarray(ref["adev"]), rtol=1e-10, atol=1e-10)


def test_error_stats():
    y_true = np.array([0.0, 1.0, 2.0])
    y_hat = np.array([0.0, 1.1, 1.9])
    stats = compute_error_statistics(y_true, y_hat)
    assert stats["rmse"] >= 0.0
    assert stats["mae"] >= 0.0
