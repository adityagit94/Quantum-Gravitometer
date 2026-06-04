"""Phase 17 — smoke tests for CI / packaging scaffolding.

These don't *run* CI — they just verify the workflow / Dockerfile files exist
and parse, so a typo doesn't ship in a release.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent


class TestGitHubActions:
    """The three workflow YAMLs must exist and parse."""

    @pytest.mark.parametrize("name", ["test.yml", "nightly.yml", "release.yml", "docs.yml"])
    def test_workflow_yaml_parses(self, name):
        path = ROOT / ".github" / "workflows" / name
        assert path.is_file(), f"missing {path}"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert isinstance(data, dict)
        assert "jobs" in data, f"{name} missing top-level 'jobs'"
        # PyYAML maps the bare workflow key 'on' to Python True, but only when
        # quoted in YAML.  Either form is acceptable.
        assert any(k in data for k in ("on", True)), f"{name} missing 'on' trigger"

    def test_test_workflow_runs_pytest_not_slow(self):
        text = (ROOT / ".github" / "workflows" / "test.yml").read_text(encoding="utf-8")
        assert "pytest" in text
        assert "not slow" in text, "fast CI must deselect @slow tests"
        assert "MPLBACKEND" in text and "Agg" in text, "needs headless matplotlib"

    def test_nightly_runs_slow_tests(self):
        text = (ROOT / ".github" / "workflows" / "nightly.yml").read_text(encoding="utf-8")
        assert "-m slow" in text


class TestPackaging:
    """The Dockerfile and dockerignore must exist and look sane."""

    def test_dockerfile_exists_and_uses_python_311(self):
        path = ROOT / "Dockerfile"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "FROM python:3.11" in text
        assert "ENTRYPOINT [\"qgrav\"]" in text
        assert "MPLBACKEND=Agg" in text

    def test_dockerignore_excludes_runs_and_research(self):
        path = ROOT / ".dockerignore"
        assert path.is_file()
        text = path.read_text(encoding="utf-8")
        assert "runs" in text
        assert "docs/research" in text  # research files are 500+ KB of MD
