"""
Hatch build hook - bundles ./skills into the wheel and records the git commit
of the skill sources (R-PKG-001..004).

Commit lookup order: git HEAD of this checkout, then _build_info.json at the
sdist root (written when the sdist was built from git), then the env vars
SKILLS_COMMIT (container build) and GITHUB_SHA, then "unknown".
"""
from __future__ import annotations

import json
import os
import shutil
# fixed git command, no user input
import subprocess  # nosec B404
import tempfile
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface

ROOT_INFO = "_build_info.json"


def _git_head(root: Path) -> str | None:
    if not (root / ".git").exists():
        return None
    git = shutil.which("git")
    if git is None:
        return None
    try:
        # fixed command, no user input
        out = subprocess.run(  # nosec B603
            [git, "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return out.stdout.strip() or None


def skills_commit(root: Path) -> str:
    head = _git_head(root)
    if head:
        return head
    info = root / ROOT_INFO
    if info.is_file():
        try:
            return str(json.loads(info.read_text(encoding="utf-8"))["skills_commit"])
        except (ValueError, KeyError):
            pass
    return os.environ.get("SKILLS_COMMIT") or os.environ.get("GITHUB_SHA") or "unknown"


class CustomBuildHook(BuildHookInterface):
    def initialize(self, version: str, build_data: dict) -> None:
        root = Path(self.root)
        self._tmp = tempfile.mkdtemp(prefix="sw-dev-agent-build-")
        info_file = Path(self._tmp) / ROOT_INFO
        info_file.write_text(
            json.dumps({"skills_commit": skills_commit(root)}) + "\n", encoding="utf-8"
        )
        if self.target_name == "sdist":
            build_data["force_include"][str(info_file)] = ROOT_INFO
        elif self.target_name == "wheel" and version != "editable":
            build_data["force_include"][str(root / "skills")] = "sw_dev_agent/skills"
            build_data["force_include"][str(info_file)] = "sw_dev_agent/_build_info.json"

    def finalize(self, version: str, build_data: dict, artifact_path: str) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)
