from pathlib import Path

import numpy as np

from qgrav.bench_ifo.real_ifo import load_real_ifo_csv
from qgrav.datasets.gravimetry import _gap_report, load_real_gravity_dataset


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
