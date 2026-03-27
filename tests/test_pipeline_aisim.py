import json
from pathlib import Path

from qgrav.pipeline import run_pipeline

CFG = """
output:
  runs_dir: runs
  name: test_pipeline_aisim
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
  metrics_backend: auto
  psd_method: welch
  welch_nperseg: 256
  welch_noverlap: 128
  allan_data_type: freq
simulation:
  enabled: true
  backend: aisim
  model: rabi_scan
  n_atoms: 120
  seed: 1
  tau_step_s: 1.0e-6
  n_steps: 10
"""

def test_pipeline_creates_aisim_outputs(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(CFG, encoding="utf-8")
    report = run_pipeline(cfg)
    metrics = json.loads((report.parent / "metrics.json").read_text())
    assert metrics["simulation"]["backend"] == "aisim"
    assert (report.parent / "plots" / "simulation_primary.png").exists()
