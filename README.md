# SW Dev Agent Framework

An agentic framework that does exactly one thing: **software development**.

Built with TDD. Every line of production code was preceded by a failing test.

## What it is

A set of agent skills covering the full software development lifecycle,
plus a Python CLI orchestrator that coordinates them.

The framework is a living example of the pattern it encodes:
it was built using the same TDD process it teaches agents to follow.

## Skills

| Phase | Skill | Purpose |
|---|---|---|
| Orchestrator | `orchestrate-sw-dev-en` | Coordinates all phases below, in this order |
| 1. Requirements | `gather-requirements-en` | Goal -> testable requirements |
| 2. Design | `design-architecture-en` | Requirements -> architecture |
| 3. Implement | `apply-tdd-loop-en` | Architecture -> tested code |
| 4. Review | `code-review-en` | Code -> reviewed + gated |
| 5. Release | `release-sw-project-en` | Reviewed code -> tagged release |

All skills follow the [agentskills.io specification](https://agentskills.io/specification).

## Install

```bash
uv tool install sw-dev-agent-framework            # CLI + skills API
uv tool install "sw-dev-agent-framework[mcp]"     # + MCP server
```

Development install from a clone:

```bash
uv sync --dev --all-extras
```

## Usage

### Pipeline CLI

```bash
sw-dev-agent start "Build a Python CLI tool that converts CSV to Markdown tables"
sw-dev-agent status
sw-dev-agent phases
sw-dev-agent --install-completion
```

### Skills API (no git clone needed)

```bash
sw-dev-agent serve                 # http://127.0.0.1:8765
sw-dev-agent serve --port 0        # free port, URL is printed
SW_DEV_AGENT_PORT=9000 sw-dev-agent serve
```

| Path | Returns |
|---|---|
| `GET /skills` | JSON list: name, description, path |
| `GET /skills/orchestrator` | `orchestrate-sw-dev-en` SKILL.md (text/markdown) |
| `GET /skills/{name}` | any skill's SKILL.md (text/markdown) |
| `GET /version` | package version and skills source commit |
| `GET /health` | `{"status": "ok"}` |
| `GET /openapi.json` | the API contract |

An agent starts with `/skills/orchestrator` and fetches each sub-skill it
names via `/skills/{name}`. Skills are returned unchanged.

### MCP server (extra `[mcp]`)

One MCP tool per API operation: `list_skills`, `get_orchestrator_skill`,
`get_skill`, `get_version`, `get_health`.

```bash
sw-dev-agent mcp                   # http://127.0.0.1:8765/sw-dev-agent-framework/mcp
sw-dev-agent mcp --stdio           # for clients that start MCP servers as a subprocess
```

Example for Claude Code:

```bash
claude mcp add sw-dev-agent -- sw-dev-agent mcp --stdio
```

### Container (Podman)

```bash
./podman_build.sh                  # reentrant
./podman_run.sh                    # API on 127.0.0.1:8765, replaces an existing container
./podman_run.sh mcp                # MCP server instead
```

## Architecture

```
sw-dev-agent-framework/
- skills/                    one SKILL.md per skill (bundled into the wheel)
- src/sw_dev_agent/
  - phases.py, orchestrator.py   pipeline model
  - cli.py                       start, status, phases, serve, mcp
  - openapi.json                 API contract (API first)
  - catalog.py                   reads bundled skills
  - api.py                       Connexion v3 app
  - server.py                    host/port handling
  - mcp_server.py                OpenAPI -> MCP tools, 1:1
  - build_info.py                version + skills commit
- hatch_build.py             bundles skills, records commit
- Dockerfile, entrypoint.sh, podman_build.sh, podman_run.sh
- tests/                     unit, API, MCP, build, container, e2e
- docs/issue-23/             requirements, architecture, review of 2.0.0
```

## TDD Build History

RED -> GREEN -> REFACTOR:

1. Phase model (phases.py)
2. Orchestrator + HandoverState (orchestrator.py)
3. Skill spec compliance (all six skills)
4. 2.0.0: catalog, packaging, API, CLI serve, MCP adapter, container
   files, license metadata - built with this framework's own skills
   (see `docs/issue-23/`)

## License

Skills: CC BY-NC-SA 4.0 | Code: MIT

See `LICENSE` and `LICENSES/`. SPDX: `MIT AND CC-BY-NC-SA-4.0`.
