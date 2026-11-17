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
| R-CTR-001..005 | tests/test_container_files.py (static) | yes | real build/run/healthcheck/reentrancy only in CI job `container` |
| R-CI-001..004, 007 | CI jobs test, sast, e2e | yes (local) | bandit 0 findings, semgrep 0 findings, e2e OK on 3.12 and 3.13 |
| R-CI-005, 006 | CI job `container` | PENDING CI | Trivy and ZAP not installed locally |

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

Minor / follow-up (not blocking 2.0.0):

1. Scanner images in CI use `:latest` (semgrep, trivy, zap) - pin versions later - .github/workflows/ci.yml - minor
2. MCP over HTTP in container mode runs without DNS-rebinding host checks (bind 0.0.0.0 inside); mitigated by publishing on 127.0.0.1 only - src/sw_dev_agent/mcp_server.py - minor
3. FIXED: release.yml step "Create GitHub Release" only uploaded a workflow artifact; now a real GitHub Release with the CHANGELOG section as notes - .github/workflows/release.yml - minor

```yaml
phase: review
status: done
output: review-checklist.md - 0 critical, 0 major, 3 minor findings; R-CI-005/006 pending CI run
```
