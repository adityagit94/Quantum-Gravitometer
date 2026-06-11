from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

_TEMPLATE = """<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>qgrav report</title>
  <style>
    body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 24px; line-height: 1.45; background: #fbfcfe; color: #202632; }
    h1, h2, h3 { color: #183153; }
    code, pre { background: #f4f6fb; padding: 2px 4px; border-radius: 4px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
    .cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
    .card { border: 1px solid #dbe2ef; border-radius: 12px; padding: 12px 14px; background: #fff; box-shadow: 0 4px 12px rgba(0,0,0,0.03); }
    .metric { font-size: 1.3rem; font-weight: 700; }
    img { max-width: 100%; height: auto; border: 1px solid #eee; border-radius: 8px; background: #fff; }
    table { border-collapse: collapse; width: 100%; background: #fff; }
    td, th { border: 1px solid #dbe2ef; padding: 8px; font-size: 14px; vertical-align: top; }
    th { background: #f6f8fc; text-align: left; }
    .muted { color: #56657f; }
    ul { padding-left: 20px; }
    .scope-panel { padding: 12px 16px; border-radius: 10px; margin: 12px 0; border: 1px solid; }
    .scope-fully-simulated { background: #e8f6ec; border-color: #44b463; color: #143a1f; }
    .scope-hybrid { background: #fff7e0; border-color: #d6a417; color: #4d3402; }
    .scope-analytical { background: #e8eef9; border-color: #4a6fb5; color: #0f213f; }
    .level-banner { padding: 10px 14px; border-radius: 8px; margin: 10px 0; border: 1px solid #c95757; background: #fdecec; color: #61130f; }
    .format-footer { margin-top: 32px; padding-top: 14px; border-top: 1px solid #dbe2ef; color: #56657f; font-size: 12px; }
  </style>
</head>
<body>
  <h1>qgrav run report</h1>
  <p class="muted">Generated from a single YAML config and saved alongside raw outputs for reproducibility.</p>

  {% if metrics.get('corrections_warnings') %}
  <div style="background:#fce4e4;border:1px solid #c00;padding:10px 14px;border-radius:6px;margin:12px 0;">
    <strong style="color:#900;">&#9888; Corrections warnings</strong>
    <ul style="margin:4px 0 0 16px;">
      {% for w in metrics.corrections_warnings %}
      <li>{{ w }}</li>
      {% endfor %}
    </ul>
  </div>
  {% endif %}

  <div class="cards">
    <div class="card"><div class="muted">Bench type</div><div class="metric">{{ metrics.bench_type }}</div></div>
    <div class="card"><div class="muted">Sample rate</div><div class="metric">{{ metrics.sample_rate_hz }}</div><div class="muted">Hz</div></div>
    <div class="card"><div class="muted">PSD method</div><div class="metric">{{ metrics.psd_method }}</div></div>
    <div class="card"><div class="muted">Allan backend</div><div class="metric">{{ metrics.allan_backend_used }}</div><div class="muted">data_type={{ metrics.allan_data_type }}</div></div>
  </div>

  {% if metrics.bench_type == 'real_gravity' %}
  <h2>Real gravimetry dataset</h2>
  <table>
    <tr><th>Station code</th><td>{{ metrics.station_code }}</td></tr>
    <tr><th>Source</th><td>{{ metrics.source_path }}</td></tr>
    <tr><th>Record start</th><td>{{ metrics.record_start }}</td></tr>
    <tr><th>Record end</th><td>{{ metrics.record_end }}</td></tr>
    <tr><th>Longitude</th><td>{{ metrics.longitude_deg }}</td></tr>
    <tr><th>Latitude</th><td>{{ metrics.latitude_deg }}</td></tr>
    <tr><th>Mean</th><td>{{ metrics.gravity_summary.mean }}</td></tr>
    <tr><th>Std</th><td>{{ metrics.gravity_summary.std }}</td></tr>
    <tr><th>Gap count</th><td>{{ metrics.gap_report.gap_count }}</td></tr>
    <tr><th>Reverse timestamps</th><td>{{ metrics.gap_report.reverse_count }}</td></tr>
    <tr><th>Missing samples estimate</th><td>{{ metrics.gap_report.missing_samples_estimate }}</td></tr>
    <tr><th>Dropped malformed rows</th><td>{{ metrics.dropped_rows }}</td></tr>
    <tr><th>Largest contiguous segment</th><td>{{ metrics.gap_report.largest_contiguous_segment_samples }}</td></tr>
    <tr><th>Analysis segment</th><td>{{ metrics.analysis_segment.segment_start }} → {{ metrics.analysis_segment.segment_end }} ({{ metrics.analysis_segment.segment_samples }} samples)</td></tr>
    <tr><th>Units</th><td>{{ metrics.series_units }}</td></tr>
  </table>
  {% if metrics.unit_warnings %}
  <h3>Unit warnings</h3>
  <ul>{% for item in metrics.unit_warnings %}<li>{{ item }}</li>{% endfor %}</ul>
  {% endif %}
  {% elif metrics.have_truth %}
  <h2>Error metrics</h2>
  <table>
    <tr><th>Metric</th><th>Baseline</th><th>Improved</th><th>Improvement %</th></tr>
    <tr><td>RMSE</td><td>{{ metrics.baseline.rmse }}</td><td>{{ metrics.improved.rmse }}</td><td>{{ metrics.rmse_improvement_percent }}</td></tr>
    <tr><td>MAE</td><td>{{ metrics.baseline.mae }}</td><td>{{ metrics.improved.mae }}</td><td>{{ metrics.mae_improvement_percent }}</td></tr>
    <tr><td>Bias</td><td>{{ metrics.baseline.bias }}</td><td>{{ metrics.improved.bias }}</td><td>—</td></tr>
    <tr><td>Error std</td><td>{{ metrics.baseline.error_std }}</td><td>{{ metrics.improved.error_std }}</td><td>—</td></tr>
    <tr><td>Time correlation</td><td>{{ metrics.baseline.time_corr }}</td><td>{{ metrics.improved.time_corr }}</td><td>—</td></tr>
    <tr><td>SNR (dB)</td><td>{{ metrics.baseline.snr_db }}</td><td>{{ metrics.improved.snr_db }}</td><td>—</td></tr>
    <tr><td>PSD corr vs truth</td><td>{{ metrics.psd_vs_truth_baseline.corr }}</td><td>{{ metrics.psd_vs_truth_improved.corr }}</td><td>—</td></tr>
    <tr><td>PSD R² vs truth</td><td>{{ metrics.psd_vs_truth_baseline.r2 }}</td><td>{{ metrics.psd_vs_truth_improved.r2 }}</td><td>—</td></tr>
  </table>
  {% else %}
  <h2>No ground-truth displacement</h2>
  <p>This run used real or externally loaded data without a reference displacement trace, so the report focuses on spectral and stability summaries.</p>
  {% endif %}

  {% if metrics.bench_type == 'real_gravity' %}
    {% if metrics.data_product_level_at_analysis is defined %}
      {% if metrics.data_product_level_at_analysis < 3 %}
        <div class="level-banner">
          <strong>Data product level {{ metrics.data_product_level_at_analysis }} detected.</strong>
          Allan deviation may be dominated by un-removed tides and pressure
          loading. Published superconducting-gravimeter noise floors assume
          Level-3 (post-correction) data. Enable
          <code>bench_real_gravity.apply_corrections: true</code> with station
          coordinates to subtract the solid-earth tide before analysis.
        </div>
      {% endif %}
      {% if metrics.corrections_applied %}
        <h2>Corrections applied</h2>
        <table>
          <tr><th>Data product level at analysis</th><td>{{ metrics.data_product_level_at_analysis }}</td></tr>
          <tr><th>Corrections</th><td>{{ metrics.corrections_applied | join(', ') }}</td></tr>
          {% for key, value in metrics.correction_metrics.items() %}
            <tr><th>{{ key }}</th><td>{{ value }}</td></tr>
          {% endfor %}
        </table>
      {% endif %}
    {% endif %}
  {% endif %}

  {% if metrics.simulation %}
  {% set scope_cat = metrics.simulation.get('study_scope_category', 'FULLY_SIMULATED') %}
  {% if scope_cat == 'HYBRID_AISIM_PLUS_ANALYTICAL' %}
    <div class="scope-panel scope-hybrid">
      <strong>Study scope: Hybrid (AISim + analytical)</strong>
      <p>{{ metrics.simulation.get('study_scope_description', '') }}</p>
      <p class="muted">Specifically: <code>{{ metrics.simulation.get('study_scope', '') }}</code></p>
    </div>
  {% elif scope_cat == 'ANALYTICAL_ONLY' %}
    <div class="scope-panel scope-analytical">
      <strong>Study scope: Analytical only</strong>
      <p>{{ metrics.simulation.get('study_scope_description', '') }}</p>
    </div>
  {% else %}
    <div class="scope-panel scope-fully-simulated">
      <strong>Study scope: Fully simulated</strong>
      <p>{{ metrics.simulation.get('study_scope_description', '') }}</p>
    </div>
  {% endif %}
  <h2>AISim simulation module</h2>
  <table>
    {% set sim_rows = metrics.simulation.get('summary_rows', {}) %}
    {% if sim_rows %}
      {% for key, value in sim_rows.items() %}<tr><th>{{ key }}</th><td>{{ value }}</td></tr>{% endfor %}
    {% else %}
      <tr><th>Backend</th><td>{{ metrics.simulation.backend }}</td></tr>
      <tr><th>Model</th><td>{{ metrics.simulation.model }}</td></tr>
    {% endif %}
  </table>

  {% if metrics.simulation.get('physical_model') %}
  <h3>Physical model decomposition</h3>
  <table>{% for key, value in metrics.simulation.get('physical_model', {}).items() %}<tr><th>{{ key }}</th><td>{{ value }}</td></tr>{% endfor %}</table>
  {% endif %}

  {% if metrics.simulation.get('pulse_sequence') %}
  <h3>Pulse sequence</h3>
  <table>{% for key, value in metrics.simulation.get('pulse_sequence', {}).items() %}<tr><th>{{ key }}</th><td>{{ value }}</td></tr>{% endfor %}</table>
  {% endif %}

  {% if metrics.simulation.get('truth_checks') %}
  <h3>Ground-truth validation</h3>
  <table>
    <tr><th>All checks passed</th><td>{{ metrics.simulation.truth_checks.all_passed }}</td></tr>
    <tr><th>Checks passed</th><td>{{ metrics.simulation.truth_checks.passed_count }}/{{ metrics.simulation.truth_checks.total_count }}</td></tr>
  </table>
  <table>
    <tr><th>Check</th><th>Passed</th><th>Observed</th><th>Expected</th><th>Note</th></tr>
    {% for item in metrics.simulation.truth_checks.get('checks', []) %}
      <tr><td>{{ item.name }}</td><td>{{ item.passed }}</td><td>{{ item.get('observed', '') }}</td><td>{{ item.get('expected', '') }}</td><td>{{ item.get('note', '') }}</td></tr>
    {% endfor %}
  </table>
  {% endif %}

  {% if metrics.simulation.get('limitations') %}
  <h3>Simulation limitations</h3>
  <ul>{% for item in metrics.simulation.get('limitations', []) %}<li>{{ item }}</li>{% endfor %}</ul>
  {% endif %}
  {% endif %}

  {% if metrics.systematics %}
  <h2>Systematic effects (order-of-magnitude)</h2>
  <table>
    <tr><th>Effect</th><th>Value (m/s&sup2;)</th><th>Value (&micro;Gal)</th><th>Note</th></tr>
    {% if metrics.systematics.gravity_gradient %}
    <tr><td>Gravity gradient</td><td>{{ metrics.systematics.gravity_gradient.value_m_s2 }}</td><td>{{ metrics.systematics.gravity_gradient.value_ugal }}</td><td>{{ metrics.systematics.gravity_gradient.note }}</td></tr>
    {% endif %}
    {% if metrics.systematics.coriolis %}
    <tr><td>Coriolis</td><td>{{ metrics.systematics.coriolis.value_m_s2 }}</td><td>{{ metrics.systematics.coriolis.value_ugal }}</td><td>{{ metrics.systematics.coriolis.note }}</td></tr>
    {% endif %}
    <tr><th>Total</th><td>{{ metrics.systematics.total_systematic_m_s2 }}</td><td>{{ metrics.systematics.total_systematic_ugal }}</td><td></td></tr>
  </table>
  <p class="muted">These are order-of-magnitude estimates and are NOT included in the AISim simulation.</p>
  {% endif %}

  {% if metrics.allan_backend_comparison %}
  <h2>Allan backend comparison</h2>
  <table>
    <tr><th>Primary backend</th><td>{{ metrics.allan_backend_comparison.primary_backend }}</td></tr>
    <tr><th>Reference backend</th><td>{{ metrics.allan_backend_comparison.reference_backend }}</td></tr>
    <tr><th>Data type</th><td>{{ metrics.allan_backend_comparison.data_type }}</td></tr>
    <tr><th>Common tau count</th><td>{{ metrics.allan_backend_comparison.tau_count }}</td></tr>
    <tr><th>Mean relative difference</th><td>{{ metrics.allan_backend_comparison.get('mean_rel_diff', 'n/a') }}</td></tr>
    <tr><th>Max relative difference</th><td>{{ metrics.allan_backend_comparison.get('max_rel_diff', 'n/a') }}</td></tr>
  </table>
  {% endif %}

  <h2>Plots</h2>
  <div class="grid">
    {% if metrics.bench_type == 'real_gravity' %}
      <div class="card"><h3>Gravity series</h3><img src="{{ plots.raw_png }}" alt="gravity series"></div>
      <div class="card"><h3>Histogram</h3><img src="{{ plots.displacement_png }}" alt="gravity histogram"></div>
      <div class="card"><h3>PSD</h3><img src="{{ plots.psd_png }}" alt="gravity psd"></div>
      <div class="card"><h3>Allan deviation</h3><img src="{{ plots.allan_png }}" alt="gravity allan"></div>
    {% else %}
      <div class="card"><h3>Displacement</h3><img src="{{ plots.displacement_png }}" alt="displacement plot"></div>
      <div class="card"><h3>PSD</h3><img src="{{ plots.psd_png }}" alt="psd plot"></div>
      <div class="card"><h3>Allan deviation</h3><img src="{{ plots.allan_png }}" alt="allan plot"></div>
      <div class="card"><h3>Raw interferometer channels</h3><img src="{{ plots.raw_png }}" alt="raw plot"></div>
      {% if plots.error_hist_png %}<div class="card"><h3>Error histogram</h3><img src="{{ plots.error_hist_png }}" alt="error histogram"></div>{% endif %}
    {% endif %}
    {% for item in plots.simulation_plots %}
      <div class="card"><h3>{{ item.title }}</h3><img src="{{ item.path }}" alt="{{ item.title }}"></div>
    {% endfor %}
  </div>

  <h2>Notes</h2>
  <ul>{% for note in metrics.notes %}<li>{{ note }}</li>{% endfor %}</ul>

  <h2>Config snapshot</h2>
  <pre>{{ config_text }}</pre>

  <h2>Metrics JSON</h2>
  <pre>{{ metrics_json }}</pre>

  <div class="format-footer">
    qgrav output format version: <code>{{ metrics.get('qgrav_output_format_version', '0.x') }}</code>
    &middot; qgrav version: <code>{{ metrics.get('qgrav_version', 'unknown') }}</code>
  </div>
</body>
</html>
"""


def build_html_report(
    *, run_dir: Path, config_text: str, metrics: dict[str, Any], plot_paths: dict[str, Any]
) -> Path:
    env = Environment(loader=FileSystemLoader(str(run_dir)), autoescape=True)
    template = env.from_string(_TEMPLATE)
    html = template.render(
        run_dir=str(run_dir),
        config_text=config_text,
        metrics=metrics,
        metrics_json=json.dumps(metrics, indent=2),
        plots={
            "displacement_png": plot_paths["displacement"],
            "psd_png": plot_paths["psd"],
            "allan_png": plot_paths["allan"],
            "raw_png": plot_paths["raw"],
            "error_hist_png": plot_paths.get("error_hist"),
            "simulation_plots": plot_paths.get("simulation_plots", []),
        },
    )
    out = run_dir / "report.html"
    out.write_text(html, encoding="utf-8")
    return out
