"""
Turn a Trivy JSON report into GitHub Actions error annotations, so every
finding is visible on the PR checks page (and via the public API).

Usage: python trivy_annotations.py trivy.json
Exit code 1 if the report has findings or is missing/unreadable.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


def _escape(text: str) -> str:
    return text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def findings(report: dict) -> list[tuple[str, dict]]:
    return [
        (result.get("Target", "?"), vuln)
        for result in report.get("Results") or []
        for vuln in result.get("Vulnerabilities") or []
    ]


def main(argv: list[str]) -> int:
    path = Path(argv[1])
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(f"::error title=Trivy report missing or unreadable::{_escape(str(exc))}")
        return 1
    found = findings(report)
    if not found:
        print("Trivy: no fixable HIGH/CRITICAL findings")
        return 0
    print(f"::error title=Trivy: {len(found)} fixable HIGH/CRITICAL finding(s)::"
          f"see the following annotations")
    for target, v in found:
        title = f"Trivy {v.get('Severity', '?')} {v.get('VulnerabilityID', '?')}"
        msg = (f"{v.get('PkgName', '?')} {v.get('InstalledVersion', '?')} -> fixed in "
               f"{v.get('FixedVersion', '?')} [{target}] {v.get('Title', '')}".rstrip())
        print(f"::error title={title}::{_escape(msg)}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
