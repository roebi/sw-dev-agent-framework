"""
Build information - package version and the git commit of the bundled skills.
"""
from __future__ import annotations

import json
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

DIST_NAME = "sw-dev-agent-framework"
BUILD_INFO_FILE = Path(__file__).resolve().parent / "_build_info.json"
UNKNOWN = "unknown"


def package_version() -> str:
    try:
        return version(DIST_NAME)
    except PackageNotFoundError:  # pragma: no cover - only when not installed
        return UNKNOWN


def skills_commit(path: Path = BUILD_INFO_FILE) -> str:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return str(data["skills_commit"])
    except (OSError, ValueError, KeyError, TypeError):
        return UNKNOWN
