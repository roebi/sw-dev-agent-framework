"""
Skill catalog - lists bundled skills and returns their SKILL.md unchanged.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import yaml

ORCHESTRATOR = "orchestrate-sw-dev-en"
SKILL_FILE = "SKILL.md"
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NAME_MAX_LEN = 64


class InvalidSkillName(ValueError):
    """The name does not match the skill name format."""


class SkillNotFound(LookupError):
    """No skill with this name is bundled."""


@dataclass(frozen=True)
class SkillInfo:
    name: str
    description: str
    path: str


def validate_name(name: str) -> str:
    if len(name) > NAME_MAX_LEN or not NAME_RE.match(name):
        raise InvalidSkillName(name)
    return name


def _frontmatter(text: str) -> dict:
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    data = yaml.safe_load(parts[1])
    return data if isinstance(data, dict) else {}


class SkillCatalog:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def list(self) -> list[SkillInfo]:
        skills = []
        for skill_md in sorted(self.root.glob(f"*/{SKILL_FILE}")):
            name = skill_md.parent.name
            if not NAME_RE.match(name):
                continue
            fm = _frontmatter(skill_md.read_bytes().decode("utf-8"))
            description = str(fm.get("description", "")).strip()
            skills.append(SkillInfo(name=name, description=description, path=f"/skills/{name}"))
        return skills

    def get(self, name: str) -> str:
        validate_name(name)
        skill_md = self.root / name / SKILL_FILE
        if not skill_md.is_file():
            raise SkillNotFound(name)
        return skill_md.read_bytes().decode("utf-8")

    def get_orchestrator(self) -> str:
        return self.get(ORCHESTRATOR)


def default_skills_root() -> Path:
    """Packaged skills in an installed wheel, else ./skills of the source checkout."""
    packaged = Path(__file__).resolve().parent / "skills"
    if packaged.is_dir():
        return packaged
    return Path(__file__).resolve().parents[2] / "skills"
