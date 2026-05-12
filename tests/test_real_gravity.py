from pathlib import Path

import pytest

from qgrav.config import find_project_root
from qgrav.datasets import convert_ggp_to_csv, list_stations_in_source, load_real_gravity_dataset
from qgrav.pipeline import run_pipeline

_PROJECT_ROOT = find_project_root(Path(__file__))
_DATA_DIR = _PROJECT_ROOT / 'data' / 'raw' / 'sg_sample'
_NEEDS_DATA = pytest.mark.skipif(
    not _DATA_DIR.exists(),
    reason=f"Real gravity sample data not found at {_DATA_DIR}",
)


@_NEEDS_DATA
def test_list_stations_and_load_sample_dataset():
    stations = list_stations_in_source(_DATA_DIR)
    assert any(item['station_code'] == 'ap046' for item in stations)

    data = load_real_gravity_dataset(source_path=_DATA_DIR, station_code='ap046')
    assert data['station_code'] == 'ap046'
    assert len(data['gravity_residual']) > 10
    assert data['sample_rate_hz'] > 0
    assert data['gap_report']['n_samples_total'] >= data['analysis_segment']['segment_samples']


@_NEEDS_DATA
def test_convert_ggp_to_csv(tmp_path: Path):
    out = tmp_path / 'ap046.csv'
    convert_ggp_to_csv(source_path=_DATA_DIR, output_path=out, station_code='ap046')
    assert out.exists()
    text = out.read_text(encoding='utf-8')
    assert 'timestamp,gravity_residual,station_code' in text.splitlines()[0]


@_NEEDS_DATA
def test_real_gravity_pipeline_runs():
    cfg = _PROJECT_ROOT / 'configs' / 'example_real_gravity.yaml'
    report = run_pipeline(cfg)
    assert report.exists()
    metrics = (report.parent / 'metrics.json').read_text(encoding='utf-8')
    assert 'real_gravity' in metrics
    assert 'station_code' in metrics
