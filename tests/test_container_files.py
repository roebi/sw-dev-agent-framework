"""TDD - container run mode files (R-CTR-001..005).

Static checks only; the real build/run/reentrancy is exercised in CI
(job "container").
"""
import os
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = ["entrypoint.sh", "podman_build.sh", "podman_run.sh"]


def read(name: str) -> str:
    return (REPO / name).read_text(encoding="utf-8")


@pytest.mark.parametrize("name", SCRIPTS + ["Dockerfile", ".containerignore"])
def test_file_exists(name):
    assert (REPO / name).is_file()


@pytest.mark.parametrize("name", SCRIPTS)
def test_script_is_executable_and_strict(name):
    assert os.access(REPO / name, os.X_OK)
    text = read(name)
    assert text.startswith(("#!/usr/bin/env bash\n", "#!/bin/sh\n"))
    assert "set -eu" in text


class TestDockerfile:
    def test_runs_as_non_root(self):
        users = re.findall(r"^USER\s+(\S+)", read("Dockerfile"), re.MULTILINE)
        assert users and users[-1] not in ("root", "0")

    def test_installs_mcp_extra(self):
        assert "[mcp]" in read("Dockerfile")

    def test_healthcheck_uses_health_endpoint(self):
        text = read("Dockerfile")
        assert "HEALTHCHECK" in text
        assert "/health" in read("entrypoint.sh")

    def test_runtime_applies_debian_security_updates(self):
        # Trivy finding: zlib1g CVE-2026-85091 fixed in a Debian update newer than the base image.
        runtime = read("Dockerfile").rsplit("\nFROM ", 1)[1]
        assert "apt-get upgrade" in runtime
        assert "rm -rf /var/lib/apt/lists/*" in runtime

    def test_runtime_has_no_pip(self):
        # Trivy finding: pip vendors pkg_resources from setuptools 70.3.0 (CVE-2025-47273).
        runtime = read("Dockerfile").rsplit("\nFROM ", 1)[1]
        assert "pip uninstall -y pip" in runtime

    def test_uses_entrypoint(self):
        assert "entrypoint.sh" in read("Dockerfile")


class TestEntrypoint:
    def test_supports_serve_and_mcp(self):
        text = read("entrypoint.sh")
        assert "sw-dev-agent serve" in text
        assert "sw-dev-agent mcp" in text


class TestPodmanScripts:
    def test_build_is_reentrant_by_fixed_tags(self):
        text = read("podman_build.sh")
        assert "podman build" in text
        assert "--format docker" in text  # keeps HEALTHCHECK in the image

    def test_run_replaces_existing_container(self):
        text = read("podman_run.sh")
        assert re.search(r"podman (container )?rm (-f|--force)", text)

    def test_run_publishes_on_localhost_only(self):
        text = read("podman_run.sh")
        assert re.search(r"(-p|--publish)\s+\"?127\.0\.0\.1:", text)

    def test_run_is_hardened(self):
        text = read("podman_run.sh")
        assert "--read-only" in text
        assert "--cap-drop" in text
