"""Release flow: the owner creates and publishes a GitHub Release in the web
UI with tag and name 'vX.Y.Z'; that event must drive the whole
delivery (CI gates -> PyPI -> release notes + dists) without further commits."""
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
WF = yaml.safe_load((REPO / ".github" / "workflows" / "release.yml").read_text())
TRIGGER = WF[True]  # PyYAML parses the key 'on' as True
JOBS = WF["jobs"]


def _run(job: str) -> str:
    return "\n".join(s.get("run", "") for s in JOBS[job]["steps"])


def test_triggered_by_published_github_release_only():
    assert TRIGGER == {"release": {"types": ["published"]}}


def test_version_check_accepts_tag_with_or_without_v():
    script = _run("check-version")
    assert 'tag="${GITHUB_REF_NAME#v}"' in script
    assert 'test "${version}" = "${tag}"' in script


def test_github_release_job_updates_existing_release():
    script = _run("github-release")
    assert "gh release create" not in script
    assert "gh release upload" in script and "--clobber" in script
    assert "gh release edit" in script and "--notes-file" in script


def test_publish_needs_all_gates():
    assert set(JOBS["build"]["needs"]) == {"ci", "check-version"}
    assert JOBS["publish"]["needs"] == "build"
    assert JOBS["github-release"]["needs"] == "publish"


def test_changelog_link_uses_release_tag_without_v():
    text = (REPO / "CHANGELOG.md").read_text()
    assert "[2.0.0]: https://github.com/roebi/sw-dev-agent-framework/compare/v1.2.0...v2.0.0" in text
