# Code Review Checklist - 2.0.0 (issue #23)

Reviewer: Claude (code-review-en), 2026-11-17. Owner sign-off: pending (PR review).

## Requirements Coverage

| Group | Covered by test | Test passes | Notes |
|---|---|---|---|
| R-PKG-001..004 | tests/test_build.py | yes | wheel built from source and from sdist; commit recorded |
| R-CAT-001..006 | tests/test_catalog.py | yes | traversal names rejected before any filesystem access |
| R-API-001..010 | tests/test_api.py | yes | response validation on; 400/404 problem+json; no traceback on 500 |
| R-CLI-001..007 | tests/test_server.py, tests/test_cli.py | yes | port 0, env/flag order, port in use -> exit 1 |
| R-MCP-001..006 | tests/test_mcp_server.py, tests/test_server.py | yes | tool list derived from spec; same content as HTTP |
| R-CTR-001..005 | tests/test_container_files.py (static) + CI job `container` | yes | build twice, run twice, healthcheck, smoke, MCP mode: green in CI run 44088137535 |
| R-CI-001..004, 007 | CI jobs test, sast, e2e | yes (local) | bandit 0 findings, semgrep 0 findings, e2e OK on 3.12 and 3.13 |
| R-CI-005, 006 | CI job `container` | yes | Trivy and ZAP green in CI run 44088137535 (after rework of finding 5) |

## Architecture Compliance

- [x] Module structure matches architecture.md
- [x] No module has more than one responsibility
- [x] Side effects are isolated per design (catalog root, handlers, socket and uvicorn injected or wrapped)
- Note: api.py adds ResponseHeadersMiddleware (security headers, markdown charset). Reason: Connexion's response validation compares the bare media type, so the charset is appended outside validation.

## Test Quality

- [x] Every requirement group has tests (246 tests)
- [x] Tests use descriptive names
- [x] No test depends on execution order
- [x] Coverage >= 80% (96%)

## Security

- [x] No secrets, passwords, or tokens in code or tests
- [x] All external inputs are validated (skill name pattern in spec + catalog; port range)
- [x] No arbitrary code execution from user input
- [x] Read-only API, loopback bind by default, security headers on every response
- [x] Container: non-root, read-only rootfs, cap-drop ALL, no-new-privileges, published on 127.0.0.1 only

## Code Quality

- [x] No em-dashes or long-dashes (CI check extended to docs, json, sh)
- [x] No magic numbers - DEFAULT_PORT, DEFAULT_HOST, MCP_PATH are constants
- [x] No dead code
- [x] Functions are pure where possible (resolve_port, tools_from_spec, validate_name)

## Required Fixes

None critical or major.

Minor findings - all reworked in this feature (owner decision 2026-11-17:
review findings create rework here, not follow-up issues):

| # | Finding | Location | Severity | Rework | Verified by |
|---|---|---|---|---|---|
| 1 | CI scanner images used `:latest` (semgrep, trivy, zap) | .github/workflows/ci.yml | minor | FIXED: pinned to version tag + digest (semgrep 1.184.0, trivy 0.76.2, zap-stable 2.17.0) | tests/test_workflows.py |
| 2 | MCP over HTTP had no DNS-rebinding host/origin checks when bound to 0.0.0.0 (container) | src/sw_dev_agent/mcp_server.py | minor | FIXED: localhost-only Host/Origin checks for every bind address | tests/test_mcp_server.py::TestDnsRebindingProtection |
| 3 | release.yml "Create GitHub Release" only uploaded a workflow artifact; CHANGELOG was never published | .github/workflows/release.yml | minor | FIXED: real GitHub Release with the CHANGELOG section as notes; release fails if the section is missing | tests/test_changelog.py |
| 4 | CI "Test Python 3.13" ran on 3.12 without the [mcp] extra (.python-version pin); MCP tests skipped silently, coverage 78.99% -> CI red (found in PR #24 CI run) | .github/workflows/ci.yml, tests/test_mcp_server.py | major | FIXED: UV_PYTHON per matrix entry, interpreter check step, no silent skip | CI steps replayed locally in a fresh clone on 3.12 and 3.13: 254+ passed, 96% |
| 5 | Trivy (CI): zlib1g CVE-2026-85091 HIGH in the python:3.14-slim base (fixed in Debian +deb13u1); setuptools 70.3.0 CVE-2025-47273 HIGH, vendored by pip as pkg_resources | Dockerfile | major | FIXED: Debian security updates applied in the image; pip uninstalled after installing the wheel (not needed at runtime) | tests/test_container_files.py; install-then-remove-pip simulated locally + e2e OK; CI Trivy re-run |

Not a finding: the Socket security bot comment on PR #24 lists the five new
direct dependencies (bandit, mcp, connexion, openapi-spec-validator, httpx)
with scores 96-100 and no alerts.

```yaml
phase: review
status: done
output: review-checklist.md - 0 open findings (5 found, 5 reworked); all CI gates green (run 44088137535)
```
