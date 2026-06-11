"""Tests for resolve_project_relative_path with project_root override.

Verifies that when a config file lives in a temp directory (as the GUI does),
passing an explicit project_root resolves relative paths correctly.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from qgrav.config import find_project_root, resolve_project_relative_path


def _project_root() -> Path:
    """Return the real project root (where pyproject.toml lives)."""
    return find_project_root(Path(__file__))


def test_resolve_with_explicit_project_root(tmp_path: Path):
    """When config is in a temp dir, project_root kwarg should be used."""
    # Create a fake temp config file (simulating GUI behavior)
    temp_config = tmp_path / "temp_config.yaml"
    temp_config.write_text("bench: {type: virtual}\n")

    # Without project_root: resolves relative to tmp_path (wrong)
    result_no_root = resolve_project_relative_path(temp_config, "src/qgrav/__init__.py")
    assert not Path(result_no_root).exists(), "Should not find src/qgrav/__init__.py in temp dir"

    # With project_root: resolves relative to real project (correct)
    root = _project_root()
    result_with_root = resolve_project_relative_path(
        temp_config, "src/qgrav/__init__.py", project_root=root
    )
    assert Path(
        result_with_root
    ).exists(), f"Should find src/qgrav/__init__.py via project root, got {result_with_root}"


def test_resolve_absolute_path_ignores_project_root(tmp_path: Path):
    """Absolute paths should be returned as-is regardless of project_root."""
    temp_config = tmp_path / "temp_config.yaml"
    temp_config.write_text("")
    abs_path = str(tmp_path / "some" / "absolute" / "path")
    result = resolve_project_relative_path(temp_config, abs_path, project_root=_project_root())
    assert result == abs_path


def test_resolve_none_returns_none(tmp_path: Path):
    """None input should always return None."""
    temp_config = tmp_path / "temp_config.yaml"
    temp_config.write_text("")
    assert resolve_project_relative_path(temp_config, None) is None
    assert resolve_project_relative_path(temp_config, None, project_root=_project_root()) is None


def test_resolve_config_relative_takes_precedence(tmp_path: Path):
    """If the path exists relative to the config file, that wins over project_root."""
    # Create a file next to the config
    (tmp_path / "local_data.csv").write_text("x,y\n1,2\n")
    temp_config = tmp_path / "temp_config.yaml"
    temp_config.write_text("")

    result = resolve_project_relative_path(
        temp_config, "local_data.csv", project_root=_project_root()
    )
    assert Path(result).exists()
    assert Path(result).parent == tmp_path  # resolved relative to config, not project root


def test_find_project_root_from_temp_dir():
    """find_project_root from a temp dir should NOT find our pyproject.toml."""
    with tempfile.TemporaryDirectory() as td:
        temp_file = Path(td) / "test.yaml"
        temp_file.write_text("")
        root = find_project_root(temp_file)
        # Should fall back to the temp dir itself (no pyproject.toml found)
        assert not (root / "pyproject.toml").exists() or root == Path(td)
