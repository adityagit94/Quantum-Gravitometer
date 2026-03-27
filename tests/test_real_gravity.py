from pathlib import Path

from qgrav.datasets import convert_ggp_to_csv, list_stations_in_source, load_real_gravity_dataset
from qgrav.pipeline import run_pipeline


def test_list_stations_and_load_sample_dataset():
    source = Path(__file__).resolve().parents[1] / 'data' / 'raw' / 'sg_sample'
    stations = list_stations_in_source(source)
    assert any(item['station_code'] == 'ap046' for item in stations)

    data = load_real_gravity_dataset(source_path=source, station_code='ap046')
    assert data['station_code'] == 'ap046'
    assert len(data['gravity_residual']) > 10
    assert data['sample_rate_hz'] > 0
    assert data['gap_report']['n_samples_total'] >= data['analysis_segment']['segment_samples']


def test_convert_ggp_to_csv(tmp_path: Path):
    source = Path(__file__).resolve().parents[1] / 'data' / 'raw' / 'sg_sample'
    out = tmp_path / 'ap046.csv'
    convert_ggp_to_csv(source_path=source, output_path=out, station_code='ap046')
    assert out.exists()
    text = out.read_text(encoding='utf-8')
    assert 'timestamp,gravity_residual,station_code' in text.splitlines()[0]


def test_real_gravity_pipeline_runs():
    cfg = Path(__file__).resolve().parents[1] / 'configs' / 'example_real_gravity.yaml'
    report = run_pipeline(cfg)
    assert report.exists()
    metrics = (report.parent / 'metrics.json').read_text(encoding='utf-8')
    assert 'real_gravity' in metrics
    assert 'station_code' in metrics
