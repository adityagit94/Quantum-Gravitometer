import json
from pathlib import Path

from qgrav.pipeline import run_pipeline

BASE_CFG = """
output:
  runs_dir: runs
  name: test_pipeline
bench:
  type: virtual
bench_virtual_ifo:
  wavelength_m: 1.55e-6
  sample_rate_hz: 1000
  duration_s: 2.0
  displacement_sines:
    - amplitude_m: 2.0e-9
      freq_hz: 5.0
      phase_rad: 0.0
  measurement_noise_std: 0.03
  amplitude: 1.0
  dc_offset: 0.2
  offset_drift_std_per_s: 0.04
  amplitude_drift_std_per_s: 0.01
  seed: 7
algorithms:
  improved:
    offset_tracking_alpha: 0.01
    phase_smooth_window: 21
stats:
  psd_method: welch
  welch_nperseg: 256
  welch_noverlap: 128
  allan_data_type: freq
  compare_allan_backends: true
"""


def test_pipeline_creates_report_allantools(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        BASE_CFG + "  metrics_backend: allantools\n  comparison_backend: custom\n", encoding="utf-8"
    )
    report = run_pipeline(cfg)
    metrics = json.loads((report.parent / "metrics.json").read_text())
    assert metrics["allan_backend_used"] == "allantools"


def test_pipeline_creates_report_custom(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(
        BASE_CFG + "  metrics_backend: custom\n  comparison_backend: allantools\n", encoding="utf-8"
    )
    report = run_pipeline(cfg)
    metrics = json.loads((report.parent / "metrics.json").read_text())
    assert metrics["allan_backend_used"] == "custom"
