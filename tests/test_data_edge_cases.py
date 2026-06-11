from pathlib import Path

import numpy as np
import pytest

from qgrav.bench_ifo.real_ifo import _ensure_array, _infer_sample_rate, load_real_ifo_csv
from qgrav.datasets.gravimetry import (
    _gap_report,
    _normalize_unit,
    _select_longest_contiguous_segment,
    _unit_validation,
    load_real_gravity_dataset,
)


def test_gap_report_counts_reverse_timestamps_before_sorting() -> None:
    t = np.array(
        [
            np.datetime64("2024-01-01T01:00:00"),
            np.datetime64("2024-01-01T00:00:00"),
            np.datetime64("2024-01-01T02:00:00"),
        ],
        dtype="datetime64[s]",
    )
    out = _gap_report(t)
    assert out["reverse_count"] == 1


def test_real_ifo_single_row_csv_is_normalized(tmp_path: Path) -> None:
    csv_path = tmp_path / "one_row.csv"
    csv_path.write_text("I_meas,Q_meas\n1.0,2.0\n", encoding="utf-8")
    data = load_real_ifo_csv(csv_path=csv_path, sample_rate_hz=100.0)
    assert data["t"].shape == (1,)
    assert data["I_meas"].shape == (1,)
    assert data["Q_meas"].shape == (1,)


def test_real_ifo_csv_tracks_dropped_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / "ifo_with_nan.csv"
    csv_path.write_text(
        "t,I_meas,Q_meas\n"
        "0.0,1.0,2.0\n"
        "0.01,nan,2.0\n"
        "0.02,1.0,nan\n"
        "0.03,1.0,2.0\n"
        "0.04,1.0,2.0\n",
        encoding="utf-8",
    )
    data = load_real_ifo_csv(csv_path=csv_path)
    assert data["dropped_rows"] == 2
    assert len(data["t"]) == 3


def test_real_gravity_csv_drops_bad_rows_and_reports_it(tmp_path: Path) -> None:
    csv_path = tmp_path / "gravity.csv"
    csv_path.write_text(
        "timestamp,gravity_residual,station_code\n"
        "2024-01-01 00:00:00,1.0,st001\n"
        ",2.0,st001\n"
        "2024-01-01 01:00:00,nan,st001\n"
        "2024-01-01 02:00:00,3.0,st001\n",
        encoding="utf-8",
    )
    data = load_real_gravity_dataset(source_path=csv_path)
    assert data["station_code"] == "st001"
    assert data["dropped_rows"] == 2
    assert len(data["gravity_residual_full"]) == 2


def test_unit_validation_accepts_new_nm_variants() -> None:
    vals = np.array([1.0, 2.0, 3.0])
    for unit in ("nm/s**2", "nm s-2", "nanometers/second**2", "nm/s2"):
        warnings = _unit_validation(vals, declared_units=unit)
        assert not any("Unrecognized" in w for w in warnings), f"Unit {unit!r} was not recognized"


def test_unit_validation_still_warns_unknown() -> None:
    vals = np.array([1.0, 2.0])
    warnings = _unit_validation(vals, declared_units="furlongs/fortnight")
    assert any("Unrecognized" in w for w in warnings)


def test_gap_detection_tolerates_timing_jitter():
    """Gap detection should not fragment a series when timestamps have small jitter."""
    base = np.datetime64("2024-01-01T00:00:00")
    # 10 samples at 60-second spacing, but with ±3 second jitter.
    timestamps = np.array([base + np.timedelta64(i * 60, "s") for i in range(10)])
    # Add jitter to some samples (within 10% of 60 s)
    timestamps[3] += np.timedelta64(3, "s")  # 63 s gap
    timestamps[7] -= np.timedelta64(5, "s")  # 55 s gap from prev

    values = np.arange(10, dtype=np.float64)

    # With tolerance=0.1 (default), 10% of 60 = 6 s tolerance → jitter ≤6 s is accepted.
    _, seg_vals, info = _select_longest_contiguous_segment(
        timestamps,
        values,
        expected_dt_s=60,
        gap_tolerance_fraction=0.1,
    )
    # All 10 samples should be in the longest segment (no spurious breaks).
    assert len(seg_vals) == 10, f"Expected 10 samples but got {len(seg_vals)} (info: {info})"

    # With tolerance=0.0, exact matching → jittered samples break the segment.
    _, seg_vals_strict, _ = _select_longest_contiguous_segment(
        timestamps,
        values,
        expected_dt_s=60,
        gap_tolerance_fraction=0.0,
    )
    assert len(seg_vals_strict) < 10, "Strict tolerance should fragment the jittered series"


def test_normalize_unit_canonical_forms():
    """_normalize_unit should map various spellings to canonical keys."""
    assert _normalize_unit("ugal") == "ugal"
    assert _normalize_unit("µgal") == "ugal"
    assert _normalize_unit("microgal") == "ugal"
    assert _normalize_unit("nm/s**2") == "nm/s^2"
    assert _normalize_unit("nm s-2") == "nm/s^2"
    assert _normalize_unit("nanometers/second**2") == "nm/s^2"
    assert _normalize_unit("m/s^2") == "m/s^2"
    assert _normalize_unit("ms^-2") == "m/s^2"
    assert _normalize_unit("  NM/S2  ") == "nm/s^2"


def test_normalize_unit_unknown_passthrough():
    """Unknown unit strings should pass through lowered and stripped."""
    assert _normalize_unit("furlongs/fortnight") == "furlongs/fortnight"


# ----------------------------------------------------------------------
# Targeted real_ifo coverage: headerless formats and error branches
# ----------------------------------------------------------------------
def test_real_ifo_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_real_ifo_csv(csv_path=tmp_path / "nope.csv")


def test_real_ifo_missing_required_column_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "no_q.csv"
    csv_path.write_text("t,I_meas\n0.0,1.0\n0.01,1.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Missing required columns"):
        load_real_ifo_csv(csv_path=csv_path)


def test_real_ifo_header_no_t_and_no_rate_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "no_t.csv"
    csv_path.write_text("I_meas,Q_meas\n1.0,2.0\n1.1,2.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sample_rate_hz"):
        load_real_ifo_csv(csv_path=csv_path)


def test_real_ifo_header_with_x_true_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "with_truth.csv"
    csv_path.write_text(
        "t,I_meas,Q_meas,x_true\n0.0,1.0,2.0,0.5\n0.01,1.1,2.1,nan\n0.02,1.2,2.2,0.7\n",
        encoding="utf-8",
    )
    data = load_real_ifo_csv(csv_path=csv_path)
    # The NaN x_true row is dropped by the finite mask.
    assert data["dropped_rows"] == 1
    assert data["x_true"].tolist() == [0.5, 0.7]


def test_real_ifo_headerless_two_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "two_col.csv"
    csv_path.write_text("1.0,2.0\n1.1,2.1\n1.2,2.2\n", encoding="utf-8")
    data = load_real_ifo_csv(csv_path=csv_path, sample_rate_hz=100.0, has_header=False)
    assert data["I_meas"].tolist() == [1.0, 1.1, 1.2]
    assert data["Q_meas"].tolist() == [2.0, 2.1, 2.2]
    np.testing.assert_allclose(np.diff(data["t"]), 0.01)


def test_real_ifo_headerless_two_columns_needs_rate(tmp_path: Path) -> None:
    csv_path = tmp_path / "two_col_no_rate.csv"
    csv_path.write_text("1.0,2.0\n1.1,2.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="sample_rate_hz"):
        load_real_ifo_csv(csv_path=csv_path, has_header=False)


def test_real_ifo_headerless_three_columns(tmp_path: Path) -> None:
    csv_path = tmp_path / "three_col.csv"
    csv_path.write_text("0.0,1.0,2.0\n0.5,1.1,2.1\n1.0,1.2,2.2\n", encoding="utf-8")
    data = load_real_ifo_csv(csv_path=csv_path, has_header=False)
    assert data["t"].tolist() == [0.0, 0.5, 1.0]
    assert float(data["sample_rate_hz"][0]) == pytest.approx(2.0)


def test_real_ifo_headerless_four_columns_with_truth(tmp_path: Path) -> None:
    csv_path = tmp_path / "four_col.csv"
    csv_path.write_text("0.0,1.0,2.0,0.1\n0.5,1.1,2.1,0.2\n", encoding="utf-8")
    data = load_real_ifo_csv(csv_path=csv_path, has_header=False)
    assert data["x_true"].tolist() == [0.1, 0.2]


def test_real_ifo_headerless_flat_input_treated_as_one_row(tmp_path: Path) -> None:
    # A 1-D parse (single column over two lines) is normalized to one row,
    # so the two values become a single (I, Q) sample.
    csv_path = tmp_path / "one_col.csv"
    csv_path.write_text("1.0\n2.0\n", encoding="utf-8")
    data = load_real_ifo_csv(csv_path=csv_path, sample_rate_hz=10.0, has_header=False)
    assert data["I_meas"].tolist() == [1.0]
    assert data["Q_meas"].tolist() == [2.0]


def test_real_ifo_headerless_single_scalar_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "scalar.csv"
    csv_path.write_text("1.0\n", encoding="utf-8")
    with pytest.raises(ValueError, match="at least 2 columns"):
        load_real_ifo_csv(csv_path=csv_path, has_header=False)


def test_real_ifo_all_rows_invalid_raises(tmp_path: Path) -> None:
    csv_path = tmp_path / "all_nan.csv"
    csv_path.write_text("t,I_meas,Q_meas\n0.0,nan,2.0\n0.01,1.0,nan\n", encoding="utf-8")
    with pytest.raises(ValueError, match="No valid finite rows"):
        load_real_ifo_csv(csv_path=csv_path)


def test_real_ifo_reverse_timestamps_raise(tmp_path: Path) -> None:
    csv_path = tmp_path / "reverse_t.csv"
    csv_path.write_text("t,I_meas,Q_meas\n0.02,1.0,2.0\n0.01,1.1,2.1\n", encoding="utf-8")
    with pytest.raises(ValueError, match="monotonic"):
        load_real_ifo_csv(csv_path=csv_path)


def test_infer_sample_rate_too_few_samples() -> None:
    with pytest.raises(ValueError, match="at least two"):
        _infer_sample_rate(np.array([0.0]))


def test_infer_sample_rate_non_finite_spacing() -> None:
    with pytest.raises(ValueError, match="non-finite"):
        _infer_sample_rate(np.array([0.0, np.inf]))


def test_infer_sample_rate_no_positive_spacing() -> None:
    with pytest.raises(ValueError, match="Cannot infer"):
        _infer_sample_rate(np.array([1.0, 1.0, 1.0]))


def test_infer_sample_rate_median_spacing() -> None:
    assert _infer_sample_rate(np.array([0.0, 0.1, 0.2, 0.3])) == pytest.approx(10.0)


def test_ensure_array_scalar_promoted_to_1d() -> None:
    out = _ensure_array(3.5)
    assert out.shape == (1,)
    assert out[0] == 3.5
