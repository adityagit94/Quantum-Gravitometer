from pathlib import Path

from qgrav.pipeline import run_pipeline
from qgrav.visuals import available_plot_kinds, build_run_figure, load_run_bundle

CFG = """
output:
  runs_dir: runs
  name: test_visuals
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
  metrics_backend: custom
  psd_method: welch
  welch_nperseg: 256
  welch_noverlap: 128
  allan_data_type: freq
simulation:
  enabled: true
  backend: aisim
  model: rabi_scan
  n_atoms: 100
  seed: 1
  tau_step_s: 1.0e-6
  n_steps: 8
"""


def test_visual_builder_handles_dashboard_and_simulation(tmp_path: Path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text(CFG, encoding="utf-8")
    report = run_pipeline(cfg)
    bundle = load_run_bundle(report.parent)
    kinds = available_plot_kinds(bundle)
    assert "dashboard" in kinds
    assert "simulation_primary" in kinds
    assert len(build_run_figure(bundle, "dashboard").axes) == 4
    assert len(build_run_figure(bundle, "simulation_primary").axes) == 1
