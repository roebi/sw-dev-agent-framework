"""TDD - packaging: bundled skills and build info (R-PKG-001..004, R-CI-003)."""
import json
import subprocess  # nosec B404 - test runs the project build tool
import zipfile
from pathlib import Path

import pytest

from sw_dev_agent import build_info

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"


def _repo_skill_files() -> dict[str, bytes]:
    return {
        str(p.relative_to(SKILLS)): p.read_bytes()
        for p in SKILLS.rglob("*") if p.is_file()
    }


@pytest.fixture(scope="module")
def wheel(tmp_path_factory) -> Path:
    out = tmp_path_factory.mktemp("dist")
    subprocess.run(  # nosec B603 B607 - fixed command, no user input
        ["uv", "build", "--wheel", "--out-dir", str(out), str(REPO)],
        check=True, capture_output=True,
    )
    return next(out.glob("*.whl"))


class TestWheel:
    def test_wheel_skills_identical_to_repo(self, wheel):
        prefix = "sw_dev_agent/skills/"
        with zipfile.ZipFile(wheel) as z:
            bundled = {
                n[len(prefix):]: z.read(n)
                for n in z.namelist() if n.startswith(prefix) and not n.endswith("/")
            }
        assert bundled == _repo_skill_files()

    def test_wheel_contains_openapi_json(self, wheel):
        with zipfile.ZipFile(wheel) as z:
            assert "sw_dev_agent/openapi.json" in z.namelist()

    def test_wheel_records_skills_commit(self, wheel):
        head = subprocess.run(  # nosec B603 B607
            ["git", "-C", str(REPO), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        with zipfile.ZipFile(wheel) as z:
            info = json.loads(z.read("sw_dev_agent/_build_info.json"))
        assert info["skills_commit"] == head


class TestBuildInfo:
    def test_package_version_matches_pyproject(self):
        import tomllib
        expected = tomllib.loads((REPO / "pyproject.toml").read_text())["project"]["version"]
        assert build_info.package_version() == expected

    def test_skills_commit_reads_build_info_file(self, tmp_path):
        f = tmp_path / "_build_info.json"
        f.write_text(json.dumps({"skills_commit": "abc123"}))
        assert build_info.skills_commit(f) == "abc123"

    def test_skills_commit_unknown_without_file(self, tmp_path):
        assert build_info.skills_commit(tmp_path / "missing.json") == "unknown"

    def test_skills_commit_unknown_on_broken_file(self, tmp_path):
        f = tmp_path / "_build_info.json"
        f.write_text("{not json")
        assert build_info.skills_commit(f) == "unknown"


class TestLicense:
    """G-9: Skills CC BY-NC-SA 4.0, Code MIT."""

    def _metadata(self, wheel) -> str:
        with zipfile.ZipFile(wheel) as z:
            name = next(n for n in z.namelist() if n.endswith(".dist-info/METADATA"))
            return z.read(name).decode()

    def test_license_expression(self, wheel):
        assert "License-Expression: MIT AND CC-BY-NC-SA-4.0" in self._metadata(wheel)

    def test_license_files_in_wheel(self, wheel):
        with zipfile.ZipFile(wheel) as z:
            names = z.namelist()
        assert any(n.endswith("licenses/LICENSES/MIT.txt") for n in names)
        assert any(n.endswith("licenses/LICENSES/CC-BY-NC-SA-4.0.txt") for n in names)

    def test_skills_declare_cc_license(self):
        for skill_md in SKILLS.glob("*/SKILL.md"):
            assert "license: CC BY-NC-SA 4.0" in skill_md.read_text()


class TestHookCommitLookup:
    @pytest.fixture
    def hook(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("hatch_build", REPO / "hatch_build.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod

    def test_env_skills_commit_without_git(self, hook, tmp_path, monkeypatch):
        monkeypatch.setenv("SKILLS_COMMIT", "fromenv")
        monkeypatch.setenv("GITHUB_SHA", "fromgithub")
        assert hook.skills_commit(tmp_path) == "fromenv"

    def test_github_sha_fallback(self, hook, tmp_path, monkeypatch):
        monkeypatch.delenv("SKILLS_COMMIT", raising=False)
        monkeypatch.setenv("GITHUB_SHA", "fromgithub")
        assert hook.skills_commit(tmp_path) == "fromgithub"

    def test_sdist_info_file(self, hook, tmp_path, monkeypatch):
        monkeypatch.setenv("SKILLS_COMMIT", "fromenv")
        (tmp_path / "_build_info.json").write_text('{"skills_commit": "fromsdist"}')
        assert hook.skills_commit(tmp_path) == "fromsdist"

    def test_unknown_when_nothing(self, hook, tmp_path, monkeypatch):
        monkeypatch.delenv("SKILLS_COMMIT", raising=False)
        monkeypatch.delenv("GITHUB_SHA", raising=False)
        assert hook.skills_commit(tmp_path) == "unknown"
