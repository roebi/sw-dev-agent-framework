"""TDD - SkillCatalog (R-CAT-001..006)."""
from pathlib import Path

import pytest

from sw_dev_agent.catalog import (
    ORCHESTRATOR,
    InvalidSkillName,
    SkillCatalog,
    SkillInfo,
    SkillNotFound,
    default_skills_root,
)

REPO_SKILLS = Path(__file__).resolve().parent.parent / "skills"


def write_skill(root: Path, name: str, description: str, body: str = "# Body\n") -> Path:
    d = root / name
    d.mkdir(parents=True)
    content = f"---\nname: {name}\ndescription: >\n  {description}\n---\n\n{body}"
    (d / "SKILL.md").write_bytes(content.encode("utf-8"))
    return d / "SKILL.md"


@pytest.fixture
def root(tmp_path):
    write_skill(tmp_path, "beta-skill", "Second skill.")
    write_skill(tmp_path, "alpha-skill", "First skill.")
    return tmp_path


class TestList:
    def test_lists_all_skills_sorted_by_name(self, root):
        names = [s.name for s in SkillCatalog(root).list()]
        assert names == ["alpha-skill", "beta-skill"]

    def test_reads_description_from_frontmatter(self, root):
        info = SkillCatalog(root).list()[0]
        assert info.description == "First skill."

    def test_has_api_path(self, root):
        assert SkillCatalog(root).list()[0].path == "/skills/alpha-skill"

    def test_ignores_directories_without_skill_md(self, root):
        (root / "not-a-skill").mkdir()
        assert len(SkillCatalog(root).list()) == 2

    def test_returns_skill_info(self, root):
        assert isinstance(SkillCatalog(root).list()[0], SkillInfo)


class TestGet:
    def test_returns_content_unchanged(self, tmp_path):
        body = "# Title\n\nUnicode stays: äöü\r\nCRLF stays.\n"
        path = write_skill(tmp_path, "my-skill", "Desc.", body)
        assert SkillCatalog(tmp_path).get("my-skill") == path.read_bytes().decode("utf-8")

    def test_unknown_name_raises_not_found(self, root):
        with pytest.raises(SkillNotFound):
            SkillCatalog(root).get("missing-skill")

    @pytest.mark.parametrize(
        "name",
        ["../etc", "..", "a/b", "Upper", "", "-lead", "trail-", "double--dash",
         "a" * 65, "with space", "dot.md"],
    )
    def test_invalid_name_raises(self, root, name):
        with pytest.raises(InvalidSkillName):
            SkillCatalog(root).get(name)

    def test_invalid_name_does_not_touch_filesystem(self, tmp_path, monkeypatch):
        catalog = SkillCatalog(tmp_path)

        def boom(*args, **kwargs):  # pragma: no cover - must not be called
            raise AssertionError("filesystem accessed")

        monkeypatch.setattr(Path, "read_bytes", boom)
        monkeypatch.setattr(Path, "is_file", boom)
        with pytest.raises(InvalidSkillName):
            catalog.get("../secret")


class TestOrchestrator:
    def test_orchestrator_name(self):
        assert ORCHESTRATOR == "orchestrate-sw-dev-en"

    def test_get_orchestrator(self, tmp_path):
        write_skill(tmp_path, ORCHESTRATOR, "Orch.")
        assert "name: orchestrate-sw-dev-en" in SkillCatalog(tmp_path).get_orchestrator()


class TestDefaultRoot:
    def test_default_root_contains_all_repo_skills(self):
        names = {s.name for s in SkillCatalog(default_skills_root()).list()}
        expected = {p.name for p in REPO_SKILLS.iterdir() if p.is_dir()}
        assert names == expected
        assert len(names) == 6
