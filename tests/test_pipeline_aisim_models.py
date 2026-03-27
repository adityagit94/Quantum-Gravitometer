import json
from pathlib import Path

from qgrav.pipeline import run_pipeline

PHASE_CFG = """
output:
  runs_dir: runs
  name: test_phase_scan
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
  model: mach_zehnder_phase_scan
  n_atoms: 120
  seed: 1
  tau_pi_half_s: 2.3e-5
  interferometer_time_s: 2.6e-1
  n_phase_points: 11
"""

GRAVITY_CFG = """
output:
  runs_dir: runs
  name: test_gravity_sweep
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
  model: gravity_sweep
  n_atoms: 120
  seed: 1
  tau_pi_half_s: 2.3e-5
  interferometer_time_s: 2.6e-1
  gravity_center_m_s2: 9.81
  gravity_span_m_s2: 2e-6
  n_gravity_points: 11
"""

VIB_CFG = """
output:
  runs_dir: runs
  name: test_vibration_sweep
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
  model: vibration_sensitivity_sweep
  n_atoms: 120
  seed: 1
  tau_pi_half_s: 2.3e-5
  interferometer_time_s: 2.6e-1
  gravity_ref_m_s2: 9.81
  vibration_frequency_hz: 1.0
  amplitude_max_m: 1e-8
  n_amplitude_points: 11
"""


def _run_cfg(tmp_path: Path, text: str) -> tuple[Path, dict]:
    cfg = tmp_path / "config.yaml"
    cfg.write_text(text, encoding="utf-8")
    report = run_pipeline(cfg)
    metrics = json.loads((report.parent / "metrics.json").read_text())
    return report, metrics


def test_pipeline_creates_phase_scan_outputs(tmp_path: Path):
    report, metrics = _run_cfg(tmp_path, PHASE_CFG)
    assert metrics["simulation"]["model"] == "mach_zehnder_phase_scan"
    assert metrics["simulation"]["truth_checks"]["all_passed"] is True
    assert (report.parent / "plots" / "simulation_primary.png").exists()
    assert (report.parent / "plots" / "simulation_secondary.png").exists()


def test_pipeline_creates_gravity_sweep_outputs(tmp_path: Path):
    report, metrics = _run_cfg(tmp_path, GRAVITY_CFG)
    assert metrics["simulation"]["model"] == "gravity_sweep"
    assert metrics["simulation"]["study_type"] == "hybrid_aisim_plus_analytic_gravity_phase"
    assert metrics["simulation"]["truth_checks"]["all_passed"] is True
    assert (report.parent / "plots" / "simulation_primary.png").exists()


def test_pipeline_creates_vibration_sweep_outputs(tmp_path: Path):
    report, metrics = _run_cfg(tmp_path, VIB_CFG)
    assert metrics["simulation"]["model"] == "vibration_sensitivity_sweep"
    assert metrics["simulation"]["truth_checks"]["all_passed"] is True
    assert (report.parent / "plots" / "simulation_primary.png").exists()
