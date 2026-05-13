"""
TDD - RED phase tests for skill spec compliance.
Every skill in the framework must pass agentskills.io spec validation.
"""
import os
import re
import pytest
import yaml

SKILLS_DIR = os.path.join(os.path.dirname(__file__), "..", "skills")

EXPECTED_SKILLS = [
    "orchestrate-sw-dev-en",
    "gather-requirements-en",
    "design-architecture-en",
    "code-review-en",
    "release-sw-project-en",
]

VALID_NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def load_skill_frontmatter(skill_name):
    skill_md = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
    with open(skill_md, "r") as f:
        content = f.read()
    # Extract YAML frontmatter between --- delimiters
    parts = content.split("---")
    assert len(parts) >= 3, f"No valid frontmatter in {skill_name}/SKILL.md"
    return yaml.safe_load(parts[1])


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
class TestSkillDirectoryExists:
    def test_skill_directory_exists(self, skill_name):
        path = os.path.join(SKILLS_DIR, skill_name)
        assert os.path.isdir(path), f"Missing skill directory: {skill_name}"

    def test_skill_md_exists(self, skill_name):
        path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
        assert os.path.isfile(path), f"Missing SKILL.md in: {skill_name}"


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
class TestSkillFrontmatter:
    def test_has_name_field(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        assert "name" in fm, f"{skill_name}: missing 'name' field"

    def test_name_matches_directory(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        assert fm["name"] == skill_name, (
            f"{skill_name}: name field '{fm['name']}' does not match directory"
        )

    def test_name_is_valid_format(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        name = fm["name"]
        assert len(name) <= 64, f"{skill_name}: name exceeds 64 chars"
        assert VALID_NAME_RE.match(name), (
            f"{skill_name}: name contains invalid characters: {name}"
        )
        assert not name.startswith("-"), f"{skill_name}: name starts with hyphen"
        assert not name.endswith("-"), f"{skill_name}: name ends with hyphen"
        assert "--" not in name, f"{skill_name}: name has consecutive hyphens"

    def test_has_description_field(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        assert "description" in fm, f"{skill_name}: missing 'description' field"

    def test_description_is_non_empty(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        desc = fm["description"].strip()
        assert len(desc) > 0, f"{skill_name}: description is empty"

    def test_description_max_1024_chars(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        desc = fm["description"].strip()
        assert len(desc) <= 1024, (
            f"{skill_name}: description exceeds 1024 chars ({len(desc)})"
        )

    def test_has_license_field(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        assert "license" in fm, f"{skill_name}: missing 'license' field"

    def test_license_is_cc_by_nc_sa(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        assert "CC BY-NC-SA 4.0" in fm["license"], (
            f"{skill_name}: expected CC BY-NC-SA 4.0 license"
        )

    def test_has_metadata_author(self, skill_name):
        fm = load_skill_frontmatter(skill_name)
        assert "metadata" in fm, f"{skill_name}: missing 'metadata' field"
        assert "author" in fm["metadata"], f"{skill_name}: metadata.author missing"
        assert fm["metadata"]["author"] == "roebi"


@pytest.mark.parametrize("skill_name", EXPECTED_SKILLS)
class TestSkillBody:
    def test_skill_md_body_is_not_empty(self, skill_name):
        path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
        with open(path, "r") as f:
            content = f.read()
        parts = content.split("---", 2)
        body = parts[2].strip() if len(parts) >= 3 else ""
        assert len(body) > 100, f"{skill_name}: SKILL.md body too short"

    def test_skill_md_under_500_lines(self, skill_name):
        path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
        with open(path, "r") as f:
            lines = f.readlines()
        assert len(lines) <= 500, (
            f"{skill_name}: SKILL.md exceeds 500 lines ({len(lines)})"
        )

    def test_skill_md_has_no_em_dashes(self, skill_name):
        path = os.path.join(SKILLS_DIR, skill_name, "SKILL.md")
        with open(path, "r") as f:
            content = f.read()
        assert "\u2014" not in content, (
            f"{skill_name}: SKILL.md contains em-dash (use hyphen-minus only)"
        )
        assert "\u2013" not in content, (
            f"{skill_name}: SKILL.md contains en-dash (use hyphen-minus only)"
        )
