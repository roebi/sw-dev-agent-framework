"""Trivy JSON report -> GitHub annotations (findings visible on the PR)."""
import json
import subprocess  # nosec B404 - runs the repo script under test
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "trivy_annotations.py"


def run(tmp_path, report) -> subprocess.CompletedProcess:
    f = tmp_path / "trivy.json"
    f.write_text(json.dumps(report))
    return subprocess.run(  # nosec B603 - fixed args
        [sys.executable, str(SCRIPT), str(f)], capture_output=True, text=True, check=False
    )


VULN = {
    "VulnerabilityID": "CVE-2026-0001", "PkgName": "libssl3", "InstalledVersion": "3.0.1",
    "FixedVersion": "3.0.2", "Severity": "HIGH", "Title": "bad thing",
}


def test_no_findings_exit_0(tmp_path):
    r = run(tmp_path, {"Results": [{"Target": "img (debian 13)", "Vulnerabilities": None}]})
    assert r.returncode == 0
    assert "::error" not in r.stdout


def test_findings_become_error_annotations_and_exit_1(tmp_path):
    r = run(tmp_path, {"Results": [{"Target": "img (debian 13)", "Vulnerabilities": [VULN]}]})
    assert r.returncode == 1
    assert "::error title=Trivy: 1 fixable HIGH/CRITICAL finding(s)::" in r.stdout
    assert ("::error title=Trivy HIGH CVE-2026-0001::libssl3 3.0.1 -> fixed in 3.0.2"
            " [img (debian 13)] bad thing") in r.stdout


def test_missing_report_is_error(tmp_path):
    r = subprocess.run(  # nosec B603 - fixed args
        [sys.executable, str(SCRIPT), str(tmp_path / "nope.json")],
        capture_output=True, text=True, check=False,
    )
    assert r.returncode == 1
    assert "::error title=Trivy report missing" in r.stdout


def test_annotation_text_is_escaped(tmp_path):
    v = {**VULN, "Title": "line1\nline2 100%"}
    r = run(tmp_path, {"Results": [{"Target": "t", "Vulnerabilities": [v]}]})
    assert "line1%0Aline2 100%25" in r.stdout
