from pathlib import Path

import numpy as np

from qgrav.bench_ifo.real_ifo import load_real_ifo_csv
from qgrav.datasets.gravimetry import (
    _gap_report,
    _normalize_unit,
    _select_longest_contiguous_segment,
    _unit_validation,
    load_real_gravity_dataset,
)


def test_gap_report_counts_reverse_timestamps_before_sorting() -> None:
    t = np.array([
        np.datetime64('2024-01-01T01:00:00'),
        np.datetime64('2024-01-01T00:00:00'),
        np.datetime64('2024-01-01T02:00:00'),
    ], dtype='datetime64[s]')
    out = _gap_report(t)
    assert out['reverse_count'] == 1


def test_real_ifo_single_row_csv_is_normalized(tmp_path: Path) -> None:
    csv_path = tmp_path / 'one_row.csv'
    csv_path.write_text('I_meas,Q_meas\n1.0,2.0\n', encoding='utf-8')
    data = load_real_ifo_csv(csv_path=csv_path, sample_rate_hz=100.0)
    assert data['t'].shape == (1,)
    assert data['I_meas'].shape == (1,)
    assert data['Q_meas'].shape == (1,)


def test_real_ifo_csv_tracks_dropped_rows(tmp_path: Path) -> None:
    csv_path = tmp_path / 'ifo_with_nan.csv'
    csv_path.write_text(
        't,I_meas,Q_meas\n'
        '0.0,1.0,2.0\n'
        '0.01,nan,2.0\n'
        '0.02,1.0,nan\n'
        '0.03,1.0,2.0\n'
        '0.04,1.0,2.0\n',
        encoding='utf-8',
    )
    data = load_real_ifo_csv(csv_path=csv_path)
    assert data['dropped_rows'] == 2
    assert len(data['t']) == 3


def test_real_gravity_csv_drops_bad_rows_and_reports_it(tmp_path: Path) -> None:
    csv_path = tmp_path / 'gravity.csv'
    csv_path.write_text(
        'timestamp,gravity_residual,station_code\n'
        '2024-01-01 00:00:00,1.0,st001\n'
        ',2.0,st001\n'
        '2024-01-01 01:00:00,nan,st001\n'
        '2024-01-01 02:00:00,3.0,st001\n',
        encoding='utf-8',
    )
    data = load_real_gravity_dataset(source_path=csv_path)
    assert data['station_code'] == 'st001'
    assert data['dropped_rows'] == 2
    assert len(data['gravity_residual_full']) == 2


def test_unit_validation_accepts_new_nm_variants() -> None:
    vals = np.array([1.0, 2.0, 3.0])
    for unit in ('nm/s**2', 'nm s-2', 'nanometers/second**2', 'nm/s2'):
        warnings = _unit_validation(vals, declared_units=unit)
        assert not any('Unrecognized' in w for w in warnings), f"Unit {unit!r} was not recognized"


def test_unit_validation_still_warns_unknown() -> None:
    vals = np.array([1.0, 2.0])
    warnings = _unit_validation(vals, declared_units='furlongs/fortnight')
    assert any('Unrecognized' in w for w in warnings)


def test_gap_detection_tolerates_timing_jitter():
    """Gap detection should not fragment a series when timestamps have small jitter."""
    base = np.datetime64("2024-01-01T00:00:00")
    # 10 samples at 60-second spacing, but with ±3 second jitter.
    timestamps = np.array([base + np.timedelta64(i * 60, "s") for i in range(10)])
    # Add jitter to some samples (within 10% of 60 s)
    timestamps[3] += np.timedelta64(3, "s")   # 63 s gap
    timestamps[7] -= np.timedelta64(5, "s")   # 55 s gap from prev

    values = np.arange(10, dtype=np.float64)

    # With tolerance=0.1 (default), 10% of 60 = 6 s tolerance → jitter ≤6 s is accepted.
    _, seg_vals, info = _select_longest_contiguous_segment(
        timestamps, values, expected_dt_s=60, gap_tolerance_fraction=0.1,
    )
    # All 10 samples should be in the longest segment (no spurious breaks).
    assert len(seg_vals) == 10, f"Expected 10 samples but got {len(seg_vals)} (info: {info})"

    # With tolerance=0.0, exact matching → jittered samples break the segment.
    _, seg_vals_strict, _ = _select_longest_contiguous_segment(
        timestamps, values, expected_dt_s=60, gap_tolerance_fraction=0.0,
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
