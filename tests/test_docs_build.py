"""v1.3.0 — MkDocs site + JOSS paper smoke tests.

Verifies the documentation site configuration and the JOSS paper exist and are
well-formed, so a broken nav entry or missing paper file is caught in CI.  The
actual `mkdocs build` runs in the Docs workflow; these tests are hermetic and
do not require mkdocs to be installed.
"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


class TestMkDocsConfig:
    def test_mkdocs_yml_parses(self):
        cfg = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        assert cfg["site_name"] == "qgrav"
        assert "nav" in cfg

    def test_all_nav_targets_exist(self):
        cfg = yaml.safe_load((ROOT / "mkdocs.yml").read_text(encoding="utf-8"))
        docs_dir = ROOT / cfg.get("docs_dir", "docs")

        def _walk(nav):
            for entry in nav:
                if isinstance(entry, dict):
                    for v in entry.values():
                        if isinstance(v, list):
                            yield from _walk(v)
                        else:
                            yield v
                elif isinstance(entry, str):
                    yield entry

        for target in _walk(cfg["nav"]):
            assert (docs_dir / target).is_file(), f"nav target missing: {target}"

    def test_index_exists(self):
        assert (ROOT / "docs" / "index.md").is_file()


class TestJossPaper:
    def test_paper_md_has_required_sections(self):
        text = (ROOT / "paper" / "paper.md").read_text(encoding="utf-8")
        assert "# Summary" in text
        assert "# Statement of need" in text
        # JOSS hard gate: AI usage must be disclosed.
        assert "AI-assistance disclosure" in text or "AI usage" in text.lower()

    def test_paper_bib_parses_entries(self):
        text = (ROOT / "paper" / "paper.bib").read_text(encoding="utf-8")
        for key in ("aisim", "freier2016", "qutip"):
            assert f"{{{key}," in text or f"@misc{{{key}" in text or key in text

    def test_paper_word_count_in_joss_range(self):
        text = (ROOT / "paper" / "paper.md").read_text(encoding="utf-8")
        # Strip the YAML front matter before counting.
        body = text.split("---", 2)[-1]
        words = len(body.split())
        # JOSS expects ~250-1750 words; ours should sit comfortably inside.
        assert 250 < words < 1750, f"paper is {words} words (JOSS wants 250-1750)"
