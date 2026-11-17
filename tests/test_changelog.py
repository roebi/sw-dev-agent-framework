"""Release notes come from CHANGELOG.md (GitHub Release body)."""
import subprocess  # nosec B404 - runs the repo script under test
import sys
import tomllib
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / ".github" / "scripts" / "changelog_section.py"

SAMPLE = """# Changelog

Intro.

## [2.0.0] - 2026-11-17

Text of two.

### Added

- a

## [1.2.0] - 2026-08-30

- old

[2.0.0]: https://example.invalid/compare/v1.2.0...v2.0.0
[1.2.0]: https://example.invalid/releases/tag/v1.2.0
"""


def run(version: str, path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(  # nosec B603 - fixed args
        [sys.executable, str(SCRIPT), version, str(path)],
        capture_output=True, text=True, check=False,
    )


def test_extracts_only_that_section(tmp_path):
    f = tmp_path / "CHANGELOG.md"
    f.write_text(SAMPLE)
    r = run("2.0.0", f)
    assert r.returncode == 0
    assert r.stdout == "Text of two.\n\n### Added\n\n- a\n"


def test_last_section_stops_before_link_definitions(tmp_path):
    f = tmp_path / "CHANGELOG.md"
    f.write_text(SAMPLE)
    assert run("v1.2.0", f).stdout == "- old\n"


def test_missing_version_fails(tmp_path):
    f = tmp_path / "CHANGELOG.md"
    f.write_text(SAMPLE)
    r = run("9.9.9", f)
    assert r.returncode == 1
    assert "9.9.9" in r.stderr


def test_current_version_has_changelog_section_and_link():
    version = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]
    r = run(version, REPO / "CHANGELOG.md")
    assert r.returncode == 0 and r.stdout.strip()
    assert f"\n[{version}]: https://github.com/roebi/sw-dev-agent-framework/" in (
        REPO / "CHANGELOG.md"
    ).read_text()


@pytest.mark.parametrize("key", ["Changelog", "Repository", "Issues"])
def test_project_urls(key):
    urls = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["urls"]
    assert urls[key].startswith("https://github.com/roebi/sw-dev-agent-framework")
