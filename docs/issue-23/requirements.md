# Requirements - Serve skills via OpenAPI (and optional MCP)

Status: APPROVED by owner on 2026-11-17
Source: https://github.com/roebi/sw-dev-agent-framework/issues/23

## Phase 0 - Intent

An agent installs one PyPI package (`sw-dev-agent-framework`), starts a
local service, and reads the orchestrator skill and every sub-skill as
plain Markdown over HTTP, without cloning this repository. Optionally the
same operations are offered as MCP tools, and the service can run in a
Podman container.

## Step 1 - Clarified goal

Ship the six SKILL.md files inside the Python package and serve them
unchanged through a local, read-only, OpenAPI-described HTTP API, so that
an agent can walk the orchestrator -> sub-skill chain on demand.

- Primary user: a coding agent (and the human who installs it).
- Core action: list skills, fetch one skill as Markdown.
- Platform: local CLI-started HTTP service; optional MCP endpoint;
  optional container.
- Constraints: Python >= 3.12, uv, Connexion v3, API-first, TDD,
  English only, ASCII-safe text (no em/en dashes).

## Resolved open questions (PROPOSED - confirm or override)

| # | Question | Proposed answer |
|---|---|---|
| Q1 | Install and start | `uv tool install sw-dev-agent-framework`; new subcommands on the existing CLI: `sw-dev-agent serve` (API) and `sw-dev-agent mcp` (MCP). `uvx --from sw-dev-agent-framework sw-dev-agent serve` works without extra effort. |
| Q2 | Port | Fixed default port 8765 so agent configs stay stable; `--port` flag and `SW_DEV_AGENT_PORT` env var override it; `--port 0` picks a free port. The base URL is always printed on startup. |
| Q3 | MCP packaging and transport | Package extra `[mcp]` so the base install stays small. Transport: streamable HTTP at `/sw-dev-agent-framework/mcp`, plus stdio (`sw-dev-agent mcp --stdio`) because most local agent clients start MCP servers over stdio. |
| Q4 | Versioning | Yes. `GET /version` returns the package version and the git commit the bundled skills were built from. |
| Q5 | Skill sync | `./skills` stays the single source of truth; the build includes it into the wheel (no committed copy, so no drift). A CI test builds the wheel and compares its skills with `./skills`. `available_skills.txt/.xml` are not bundled; `GET /skills` generates the list from the SKILL.md frontmatter. |
| Q6 | Non-Markdown files | Only SKILL.md in this feature. Note: three skills reference `references/*.md` files that do not exist in the repo today (see Gaps). |
| Q7 | Auth and binding | Bind to 127.0.0.1 by default; `--host` to change it. No token: content is public, read-only. Container listens on 0.0.0.0 inside, `podman_run.sh` publishes to 127.0.0.1 on the host only. |
| Q8 | Compatibility | Existing commands `start`, `status`, `phases` and the `sw_dev_agent` import API stay unchanged. Connexion and an ASGI server become base dependencies. |

## Requirement Groups

Build order derived from `depends-on`:

```
1. R-PKG  - bundled skills          depends-on: none
2. R-CAT  - skill catalog           depends-on: R-PKG
3. R-API  - OpenAPI HTTP API        depends-on: R-CAT
4. R-CLI  - start commands          depends-on: R-API
5. R-MCP  - optional MCP server     depends-on: R-API, R-CLI
6. R-CTR  - optional container      depends-on: R-CLI
7. R-CI   - CI and security gates   depends-on: R-PKG, R-API, R-MCP, R-CTR
```

### R-PKG-000 - Bundled skills
depends-on: none

R-PKG-001: Include every `skills/<name>/SKILL.md` file in the built wheel and sdist.
  driver: usability (today an agent must clone the repo to get the skills)
R-PKG-002: Provide the bundled skill files at runtime without network access and without the git repository present.
  driver: usability (agents run offline or in sandboxes without git)
R-PKG-003: Keep the bundled SKILL.md bytes identical to the files in `./skills` at build time.
  driver: usability (a silently diverged skill set gives agents wrong instructions)
R-PKG-004: Record the git commit of the skill sources in the built package.
  driver: usability (an agent cannot tell which skill set it received)

### R-CAT-000 - Skill catalog
depends-on: R-PKG

R-CAT-001: Return the list of all bundled skills with `name`, `description` and API path for each.
  driver: usability (agent needs to discover skills without knowing names upfront)
R-CAT-002: Read `name` and `description` from each SKILL.md YAML frontmatter.
  driver: usability (a second, hand-maintained index drifts from the skills)
R-CAT-003: Return the full SKILL.md content of a skill by its name.
  driver: usability (core use case: fetch one skill)
R-CAT-004: Reject a skill name that does not match `^[a-z0-9]+(-[a-z0-9]+)*$` without touching the filesystem.
  driver: usability (prevents path traversal such as `../../etc/passwd`)
R-CAT-005: Report "not found" for a valid name that is not bundled.
  driver: usability (agent needs a clear signal to stop following a chain)
R-CAT-006: Identify `orchestrate-sw-dev-en` as the orchestrator skill.
  driver: usability (the orchestrator is the entry point of the chain)

### R-API-000 - OpenAPI HTTP API
depends-on: R-CAT

R-API-001: Describe every route in a committed `openapi.json` (OpenAPI 3.x) that is approved before route code is written.
  driver: usability (API-first: agents and the MCP layer depend on a stable contract)
R-API-002: `GET /skills` returns the catalog from R-CAT-001 as `application/json`.
  driver: usability (discovery)
R-API-003: `GET /skills/orchestrator` returns the orchestrator SKILL.md unchanged as `text/markdown; charset=utf-8`.
  driver: usability (single well-known entry point)
R-API-004: `GET /skills/{name}` returns that SKILL.md unchanged as `text/markdown; charset=utf-8`.
  driver: usability (follow the chain skill by skill)
R-API-005: `GET /skills/{name}` returns 404 with a JSON problem body for an unknown name.
  driver: usability (R-CAT-005 over HTTP)
R-API-006: `GET /skills/{name}` returns 400 with a JSON problem body for an invalid name.
  driver: usability (R-CAT-004 over HTTP)
R-API-007: `GET /health` returns 200 with `{"status": "ok"}`.
  driver: usability (scripts and container healthchecks need a liveness probe)
R-API-008: `GET /version` returns the package version and the skills source commit.
  driver: usability (Q4)
R-API-009: Serve the OpenAPI document itself at `GET /openapi.json`.
  driver: usability (agents and tools can read the contract from the running service)
R-API-010: Reject request parameters and responses that do not match `openapi.json`.
  driver: usability (spec and implementation cannot drift silently)

### R-CLI-000 - Start commands
depends-on: R-API

R-CLI-001: `sw-dev-agent serve` starts the HTTP API.
  driver: usability (one command after install)
R-CLI-002: Bind to 127.0.0.1 by default; accept `--host` to override.
  driver: usability (no accidental exposure on the network)
R-CLI-003: Listen on port 8765 by default; accept `--port` and `SW_DEV_AGENT_PORT`, flag wins over env.
  driver: usability (stable URL for agent configs)
R-CLI-004: With port 0, listen on a free port chosen by the OS.
  driver: usability (avoid conflicts when 8765 is taken)
R-CLI-005: Print the base URL actually in use to stdout on startup.
  driver: usability (agent needs the URL, especially with port 0)
R-CLI-006: Exit with code 1 and a one-line error if the port is already in use.
  driver: usability (no raw stack trace)
R-CLI-007: Keep `start`, `status` and `phases` behaviour unchanged.
  driver: usability (existing users)

### R-MCP-000 - Optional MCP server
depends-on: R-API, R-CLI

R-MCP-001: Expose exactly one MCP tool per OpenAPI operation, with no extra tools and no extra behaviour.
  driver: parity (hypothesis: agents such as Claude Code connect to local tools mainly via MCP; users of those agents will prefer adding one MCP server over teaching the agent an HTTP API)
R-MCP-002: Derive the MCP tool list from `openapi.json` at startup, so a new operation becomes a new tool without code changes.
  driver: usability (issue: "transparent to spec changes")
R-MCP-003: Return the same content as the matching HTTP operation for every tool call.
  driver: usability (1:1 mapping)
R-MCP-004: `sw-dev-agent mcp` serves streamable HTTP at `http://<host>:<port>/sw-dev-agent-framework/mcp`, with the same host/port rules as R-CLI-002..006.
  driver: parity (same hypothesis as R-MCP-001)
R-MCP-005: `sw-dev-agent mcp --stdio` serves MCP over stdio.
  driver: parity (hypothesis: most local MCP clients launch servers as a stdio subprocess)
R-MCP-006: Ship MCP support as the package extra `[mcp]`; without it, `sw-dev-agent mcp` exits with code 1 and prints the install command.
  driver: usability (small base install; clear fix when the extra is missing)

### R-CTR-000 - Optional container run mode
depends-on: R-CLI

R-CTR-001: Provide a `Dockerfile` that builds an image running `sw-dev-agent serve` as a non-root user.
  driver: usability (run the service without a local Python setup)
R-CTR-002: Provide `entrypoint.sh` that starts the API by default and the MCP server when asked.
  driver: usability (one image for both modes)
R-CTR-003: Provide `podman_build.sh` that can run repeatedly with the same result and no manual cleanup.
  driver: usability (issue: reentrant scripts)
R-CTR-004: Provide `podman_run.sh` that replaces an existing container of the same name and publishes the port on 127.0.0.1 only.
  driver: usability (reentrant, local-only exposure)
R-CTR-005: Define a container healthcheck against `GET /health`.
  driver: usability (detect a dead service)

### R-CI-000 - CI and security gates
depends-on: R-PKG, R-API, R-MCP, R-CTR

R-CI-001: Validate `openapi.json` against the OpenAPI specification in CI.
  driver: usability (broken contract is caught before release)
R-CI-002: Fail CI if any implemented route is missing from `openapi.json` or any spec operation is not implemented.
  driver: usability (issue acceptance: spec matches routes)
R-CI-003: Fail CI if the built wheel's skills differ from `./skills`.
  driver: usability (R-PKG-003)
R-CI-004: Run Python SAST (bandit and semgrep) and fail on medium or higher findings.
  driver: usability (issue: security gates)
R-CI-005: Scan the container image with Trivy and fail on HIGH or CRITICAL findings with a fix available.
  driver: usability (issue: security gates)
R-CI-006: Run a DAST scan (OWASP ZAP API scan driven by `openapi.json`) against the running container and fail on medium or higher alerts.
  driver: usability (issue: security gates)
R-CI-007: Run an end-to-end test that installs the built wheel in a clean environment, starts the service, and fetches the orchestrator and all five sub-skills over HTTP.
  driver: usability (issue acceptance criterion)

## Non-Functional Requirements

NFR-01: Testability - every requirement is covered by at least one automated test; line coverage stays >= 80 % (current CI gate).
NFR-02: Performance - `GET /skills/{name}` responds in < 50 ms at the 95th percentile on a local machine (skills are small files).
NFR-03: Portability - Python 3.12 and 3.13 on Linux; macOS and Windows for `serve` (container mode Linux/Podman only).
NFR-04: Security - the service is read-only, has no write routes, and never reads files outside the bundled skills directory.
NFR-05: Reliability - unknown routes return 404, never 500; no stack traces in HTTP responses.
NFR-06: Language - all committed text in English and ASCII-safe (existing CI dash check also covers new files).
NFR-07: Stack - Connexion v3 for the HTTP API (issue constraint).

## Out of Scope

- Serving non-SKILL.md files (`references/`, `scripts/`) - may follow in a later issue.
- Write operations (creating or editing skills over the API).
- Authentication / tokens and TLS.
- Running the orchestrator pipeline (`start`/`status`) over the API.
- Publishing the container image to a registry.
- Docker (non-Podman) specific tooling beyond a standard Dockerfile.

## Gaps found while gathering (need a decision)

- G-1: `orchestrate-sw-dev-en` references `references/phase-contracts.md`, and `release-sw-project-en` references `references/semver.md` and `references/trusted-publishing.md`. None of these files exist. Proposed: out of scope here (Q6), open a separate issue.
- G-2: `tests/test_skill_spec_compliance.py` lists 5 expected skills but omits `apply-tdd-loop-en`. Proposed: fix in this feature, since R-PKG/R-CAT rely on all six skills being valid.
- G-3: CI tests Python 3.11, but `pyproject.toml` requires >= 3.12. Proposed: drop 3.11 from the CI matrix in this feature.

## Requirements Review

- [x] Dependency order respected (no group approved before its dependencies)
- [x] Every requirement has a driver
- [x] No conflicting requirements across groups
- [x] No gaps against the Phase 0 goal statement (G-1..G-3 listed above)
- [x] Parity-driven requirements have an explicit usage/adoption hypothesis (R-MCP-001, R-MCP-004, R-MCP-005)
- [x] Compliance-driven requirements reference the law/regulation and deadline (none present)
- [x] Reviewed by: roebi (owner) on 2026-11-17

## Owner decisions (2026-11-17)

- Q1-Q8: proposed answers accepted.
- G-1: fixed in this feature; per G-7 the content is inlined into the SKILL.md files.
- G-2: fixed in this feature.
- G-3: Python 3.11 removed from the CI matrix.
- G-4: this feature is released as a new major version 2.0.0.
- G-5: CHANGELOG.md is updated for 2.0.0.
- G-6: target is a 2.0.0 release on PyPI on 2026-11-17.
- G-7: every skill directory contains only SKILL.md. Reference or template
  content a skill needs is inlined into its SKILL.md. Enforced by
  `test_skill_directory_contains_only_skill_md` and
  `test_skill_md_has_no_external_file_references`. This also makes Q6 moot:
  SKILL.md is the complete skill.
