"""
Print the CHANGELOG.md section of one version (Keep a Changelog format),
without its heading. Used as the GitHub Release body.

Usage: python changelog_section.py <version|vVERSION> [CHANGELOG.md]
Exit code 1 if the version has no section.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def section(text: str, version: str) -> str | None:
    version = version.removeprefix("v")
    lines = text.splitlines()
    heading = re.compile(rf"^## \[{re.escape(version)}\]")
    start = next((i for i, line in enumerate(lines) if heading.match(line)), None)
    if start is None:
        return None
    body = []
    for line in lines[start + 1:]:
        if line.startswith("## ") or re.match(r"^\[[^\]]+\]: ", line):
            break
        body.append(line)
    return "\n".join(body).strip() + "\n"


def main(argv: list[str]) -> int:
    version = argv[1]
    path = Path(argv[2]) if len(argv) > 2 else Path("CHANGELOG.md")
    result = section(path.read_text(encoding="utf-8"), version)
    if result is None:
        print(f"No CHANGELOG section for version {version} in {path}", file=sys.stderr)
        return 1
    sys.stdout.write(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
