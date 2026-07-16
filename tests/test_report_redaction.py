"""report.html is the shareable artifact of a run, so credential-like values
must be masked in it (the verbatim config survives in config_used.yaml)."""

from __future__ import annotations

from pathlib import Path

from qgrav.reporting.report import (
    _redact_config_text,
    _redact_metrics,
    build_html_report,
)


def _minimal_metrics() -> dict:
    return {
        "bench_type": "virtual",
        "sample_rate_hz": 100.0,
        "psd_method": "welch",
        "allan_backend_used": "custom",
        "allan_data_type": "freq",
        "notes": [],
    }


def _dummy_plots(tmp_path: Path) -> dict:
    return {
        "displacement": "plots/displacement.png",
        "psd": "plots/psd.png",
        "allan": "plots/allan.png",
        "raw": "plots/raw.png",
    }


class TestRedactConfigText:
    def test_credential_like_keys_are_masked(self):
        text = (
            "bench:\n"
            "  type: real_gravity\n"
            "bench_real_gravity:\n"
            "  station_code: ap046\n"
            "  api_key: hunter2\n"
            "  access_token: abc.def.ghi\n"
        )
        redacted = _redact_config_text(text)
        assert "hunter2" not in redacted
        assert "abc.def.ghi" not in redacted
        assert redacted.count("'[redacted]'") == 2
        # Non-sensitive lines stay verbatim.
        assert "station_code: ap046" in redacted
        assert "type: real_gravity" in redacted

    def test_url_credentials_are_masked(self):
        text = (
            "bench_real_gravity:\n"
            "  source_path: https://alice:supersecret@example.com/data.zip\n"
            "  mirror: https://example.com/data.zip?token=tok123&x=1\n"
        )
        redacted = _redact_config_text(text)
        assert "supersecret" not in redacted
        assert "tok123" not in redacted
        # The whole userinfo (username included) is masked.
        assert "alice" not in redacted
        assert "https://[redacted]@example.com/data.zip" in redacted
        assert "?token=[redacted]&x=1" in redacted


class TestRedactMetrics:
    def test_nested_sensitive_keys_and_url_strings(self):
        metrics = {
            "bench_type": "virtual",
            "nested": {"api_key": "hunter2", "count": 3},
            "items": [{"password": "pw"}, "https://u:pw2@host/x"],
        }
        redacted = _redact_metrics(metrics)
        assert redacted["nested"]["api_key"] == "[redacted]"
        assert redacted["items"][0]["password"] == "[redacted]"
        assert "pw2" not in redacted["items"][1]
        # Non-sensitive values are untouched.
        assert redacted["bench_type"] == "virtual"
        assert redacted["nested"]["count"] == 3
        # The input dict is not mutated.
        assert metrics["nested"]["api_key"] == "hunter2"


def test_report_html_contains_no_secrets(tmp_path):
    config_text = (
        "bench:\n"
        "  type: virtual\n"
        "data_source:\n"
        "  url: https://bob:supersecret@example.com/d.csv?api_key=k12345\n"
        "  auth_token: tok987\n"
    )
    metrics = _minimal_metrics()
    metrics["source_path"] = "https://bob:supersecret@example.com/d.csv?api_key=k12345"
    report = build_html_report(
        run_dir=tmp_path,
        config_text=config_text,
        metrics=metrics,
        plot_paths=_dummy_plots(tmp_path),
    )
    html = report.read_text(encoding="utf-8")
    assert "supersecret" not in html
    assert "k12345" not in html
    assert "tok987" not in html
    assert "[redacted]" in html
    # The report points readers at the verbatim copy.
    assert "config_used.yaml" in html
