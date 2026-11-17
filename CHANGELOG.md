# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- MCP over streamable HTTP is stateless for all clients: clients using
  the handshake-era protocol (up to 2025-11-25) no longer get a session;
  every request stands alone, as with the stateless 2026-07-28 protocol.

### Fixed

- `sw-dev-agent --help` showed "(requires the  extra)" for the `mcp`
  command: Rich markup swallowed `[mcp]`.

## [2.0.0] - 2026-11-17

Major release: the skills are now usable with a single install, without
cloning this repository (issue #23).

### Added

- Skills API: `sw-dev-agent serve` starts a local, read-only HTTP API
  described by the bundled `openapi.json` (Connexion v3):
  `GET /skills`, `GET /skills/orchestrator`, `GET /skills/{name}`
  (SKILL.md returned unchanged as `text/markdown`), `GET /health`,
  `GET /version` (package version + skills source commit),
  `GET /openapi.json`.
- Listens on 127.0.0.1:8765 by default; `--host`, `--port` and
  `SW_DEV_AGENT_PORT` override it, `--port 0` picks a free port. The URL
  in use is printed on startup.
- MCP server (optional extra `[mcp]`): `sw-dev-agent mcp` serves one MCP
  tool per OpenAPI operation, 1:1, over streamable HTTP at
  `/sw-dev-agent-framework/mcp`, or over stdio with `--stdio`. Tools are
  generated from `openapi.json` at startup.
- All six skills are bundled into the wheel as package data (offline
  capable); the build records the git commit of the skill sources.
- Container run mode: `Dockerfile`, `entrypoint.sh`, reentrant
  `podman_build.sh` and `podman_run.sh` (non-root, read-only, published
  on 127.0.0.1 only, healthcheck).
- CI gates: OpenAPI validation, wheel content check, bandit and semgrep
  SAST, Trivy image scan, OWASP ZAP API scan (DAST) against the running
  container, end-to-end test of the installed wheel. The release
  workflow runs all CI gates and checks that the tag matches the version.
- Releases: publishing a GitHub Release (tag and name `vX.Y.Z`) starts
  the release workflow: all CI gates, version and CHANGELOG checks, PyPI
  upload, then the release notes are set to this file's section for that
  version and the wheel and sdist are attached. PyPI project links
  include the changelog.
- License files: `LICENSE`, `LICENSES/MIT.txt`,
  `LICENSES/CC-BY-NC-SA-4.0.txt`; package metadata declares
  `MIT AND CC-BY-NC-SA-4.0` (code MIT, skills CC BY-NC-SA 4.0).
- `orchestrate-sw-dev-en`: Phase Contracts section (inputs, outputs and
  exit gate per phase, send-back rules).
- `release-sw-project-en`: Semver Rules and PyPI Trusted Publishing
  setup sections.

### Changed

- Every skill directory contains only its `SKILL.md`; reference content
  that was previously pointed to under `references/` is now inlined.
- New base dependency: `connexion[uvicorn]`.
- CI tests Python 3.12, 3.13, 3.14 and 3.15 (3.11 removed; the package
  already required Python >= 3.12).
- All dependencies updated to their latest releases (pydantic 2.14,
  typer 0.29, ruff 0.17, hatchling 1.33, ...); GitHub Actions updated to
  checkout v7, setup-uv v10.3.3 (pinned by commit; setup-uv no longer
  publishes major tags), upload-artifact v7, download-artifact v8,
  pypi-publish v1.14.3 (pinned by commit); container base image
  python:3.15-slim with uv 0.13.8. Dependabot now also updates GitHub
  Actions and the Dockerfile base images.

### Security

- MCP over streamable HTTP accepts only localhost `Host` and `Origin`
  headers (DNS-rebinding protection), also when bound to 0.0.0.0 in the
  container.
- CI scanner images (semgrep, Trivy, ZAP) are pinned by version and
  digest.
- Container image: Debian security updates are applied on build
  (zlib1g CVE-2026-85091), and pip is removed after installing the
  package (its vendored setuptools 70.3.0 pkg_resources, CVE-2025-47273).
- Trivy and ZAP findings are reported as GitHub annotations.

### Fixed

- The CI job "Test Python 3.13" ran on Python 3.12 because of the
  `.python-version` pin; the matrix version is now enforced.
- The release workflow step "Create GitHub Release" only uploaded a
  workflow artifact; the published GitHub Release now gets the CHANGELOG
  notes and the dists.
- Skill spec compliance tests now cover all six skills, including
  `apply-tdd-loop-en`.
- Skills no longer reference files that did not exist.

## [1.2.0] - 2026-08-30

### Added

- `gather-requirements-en`: requirement groups now carry an explicit
  `depends-on` field; groups with no dependency are gathered and
  approved first (convention over configuration).
- `gather-requirements-en`: mandatory `driver` tag per requirement
  (`compliance` | `parity` | `usability`), with compliance requirements
  required to name the law/regulation and deadline, and parity
  requirements required to carry a usage/adoption hypothesis.
- `gather-requirements-en`: new cross-group Requirements Review step
  (Step 7) that must pass before requirements.md can freeze into the
  approved plan; checks dependency order, conflicts, gaps, and re-checks
  parity/compliance requirements.
- `gather-requirements-en`: new Phase 0 (Intent Capture) prerequisite -
  the skill now expects, and asks for if missing, an informal
  solution-oriented goal statement before deriving requirement groups.
- `gather-requirements-en`: worked example of a correct dependency order
  across primitives, shared building blocks, parallel workflows,
  integration layers, and a packaging group.

## [0.1.1] - 2026-05-13

### Added

- Initial release of the 5-phase pipeline: REQUIREMENTS -> DESIGN ->
  IMPLEMENT -> REVIEW -> RELEASE.
- `gather-requirements-en`: goal statement to numbered FR/NFR
  requirements.md, with testability/atomicity/clarity validation gates
  and an out-of-scope section.

[Unreleased]: https://github.com/roebi/sw-dev-agent-framework/compare/v2.0.0...HEAD
[2.0.0]: https://github.com/roebi/sw-dev-agent-framework/compare/v1.2.0...v2.0.0
[1.2.0]: https://github.com/roebi/sw-dev-agent-framework/compare/v0.1.1...v1.2.0
[0.1.1]: https://github.com/roebi/sw-dev-agent-framework/releases/tag/v0.1.1
