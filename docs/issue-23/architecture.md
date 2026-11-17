# Architecture - Serve skills via OpenAPI (and optional MCP)

Input: `docs/issue-23/requirements.md` (approved).

## Summary

`./skills` stays the single source. A Hatch build hook copies it into the
wheel as `sw_dev_agent/skills/` and writes the source commit into
`sw_dev_agent/_build_info.json`. A small `SkillCatalog` reads skills from a
directory that is passed in. A Connexion v3 `AsyncApp` is built from the
committed `openapi.json`; a custom resolver binds each `operationId` to a
method of a `SkillHandlers` object that holds the catalog, so there is no
global state. The MCP server is a generic adapter: it reads `openapi.json`,
creates one tool per operation, and answers each tool call by sending the
matching HTTP request in-process to the same ASGI app. Spec and MCP
therefore cannot drift. The CLI commands are thin wrappers.

## Module Structure

```
hatch_build.py                     build hook: bundle skills + build info      R-PKG-001..004
src/sw_dev_agent/
  openapi.json                     API contract (API first)                    R-API-001
  catalog.py                       SkillCatalog, name validation               R-CAT-001..006
  build_info.py                    package version + skills commit             R-PKG-004, R-API-008
  api.py                           SkillHandlers, create_app()                 R-API-002..010
  server.py                        port resolution, socket bind, uvicorn run   R-CLI-002..006
  mcp_server.py                    OpenAPI -> MCP tools adapter                R-MCP-001..005
  cli.py                           + serve, mcp commands                       R-CLI-001, R-CLI-007, R-MCP-006
Dockerfile, entrypoint.sh,
podman_build.sh, podman_run.sh                                                 R-CTR-001..005
.github/workflows/ci.yml           + spec, wheel, SAST, container, DAST, e2e   R-CI-001..007
tests/
  test_catalog.py, test_build.py, test_api.py, test_server.py,
  test_mcp_server.py, test_cli_serve.py, test_container_files.py,
  e2e/smoke_wheel.py
```

## Components

### SkillCatalog (`catalog.py`)
- Responsibility: list skills and return SKILL.md text from one root directory.
- Public interface: `SkillCatalog(root: Path)`, `.list() -> list[SkillInfo]`,
  `.get(name) -> str`, `ORCHESTRATOR = "orchestrate-sw-dev-en"`,
  `default_skills_root() -> Path`, errors `InvalidSkillName`, `SkillNotFound`.
- Name is checked against `^[a-z0-9]+(-[a-z0-9]+)*$` (max 64) before any path is built.
- Content is read as bytes and decoded UTF-8, never transformed.
- `default_skills_root()`: the packaged `sw_dev_agent/skills` if present
  (installed wheel), otherwise `<repo>/skills` (editable dev install).

### build_info (`build_info.py`)
- `package_version()` from `importlib.metadata`; `skills_commit()` from
  `_build_info.json`, or `"unknown"` if absent.

### API (`api.py`)
- `SkillHandlers(catalog, info)` with one method per operation.
- `create_app(catalog, info) -> connexion.AsyncApp`, with
  `validate_responses=True` and a resolver mapping
  `sw_dev_agent.api.handlers.<op>` to `SkillHandlers.<op>`.
- 404/400 use `application/problem+json`. Invalid names are rejected by
  the spec `pattern` (400) before the handler runs; the catalog checks again.

### Server (`server.py`)
- `resolve_port(flag, env) -> int` (flag > env > 8765), pure.
- `bind_socket(host, port) -> socket` raises `PortInUse`; binding first makes
  port 0 and "port in use" testable and gives the real URL before uvicorn starts.
- `serve(asgi_app, sock)` runs uvicorn on the given socket.

### MCP adapter (`mcp_server.py`, extra `[mcp]`)
- `tools_from_spec(spec) -> list[ToolSpec]`: one per operation; tool name =
  last segment of `operationId`; path parameters become required string input fields.
- `build_mcp_server(spec, asgi_app) -> mcp.server.lowlevel.Server` whose
  `call_tool` sends the request through `httpx.ASGITransport` to `asgi_app`
  and returns the body as text content (`isError` for non-2xx).
- `mcp_http_app(server) -> Starlette` mounted at `/sw-dev-agent-framework/mcp`; stdio via `mcp.server.stdio.stdio_server`.

## Data Flow

```
agent --GET /skills/{name}--> uvicorn -> Connexion (validate request vs openapi.json)
      -> SkillHandlers.get_skill -> SkillCatalog.get -> file bytes
      -> Connexion (validate response) -> text/markdown
agent --MCP tools/call get_skill{name}--> MCP Server -> httpx ASGITransport
      -> same Connexion app as above -> text content
```

## Technology Choices

| Decision | Choice | Rationale |
|---|---|---|
| HTTP framework | Connexion 3 `AsyncApp` + uvicorn | issue constraint; spec-driven validation |
| MCP | official `mcp` SDK 2.x lowlevel `Server` | generic tool list from the spec; no decorators per tool |
| MCP -> API call | `httpx.ASGITransport`, in-process | exact 1:1 behaviour, no second port |
| Bundling | Hatch build hook + `force_include` | no committed copy of skills, no drift |
| SAST | bandit, semgrep (`p/python`) | issue constraint |
| Image scan | Trivy | issue constraint |
| DAST | OWASP ZAP API scan with `openapi.json` | spec-driven, runs against the container |
| Container | `python:3.13-slim`, non-root, wheel install | small, mirrors the PyPI install |

## Testability Constraints

- Catalog takes `root: Path`; tests use `tmp_path` skill trees.
- Handlers get the catalog by constructor injection; API tests use
  Connexion's `test_client()` with a fake catalog.
- Port and socket logic is pure or takes host/port; no uvicorn needed in unit tests.
- MCP tests connect `mcp.Client(server)` in-process.
- Build hook tested by building the wheel in a temp dir and comparing files with `./skills`.

## Open Questions

- None.
