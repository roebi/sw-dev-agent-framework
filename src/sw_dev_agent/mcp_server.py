"""
MCP adapter - exposes every OpenAPI operation as one MCP tool, 1:1.

Tools are derived from openapi.json at startup (R-MCP-002). A tool call is
sent as the matching HTTP request, in-process, to the same Connexion app
that serves the HTTP API (R-MCP-003), so both always return the same
content. Requires the [mcp] extra.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote

import anyio
import httpx
import mcp_types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from starlette.applications import Starlette

from sw_dev_agent.api import SPEC_PATH, BuildInfo, create_app
from sw_dev_agent.catalog import SkillCatalog, default_skills_root
from sw_dev_agent.server import MCP_PATH

SERVER_NAME = "sw-dev-agent-framework"
HTTP_METHODS = ("get", "put", "post", "delete", "patch", "head", "options")


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    method: str
    path: str
    path_params: tuple[str, ...]
    input_schema: dict[str, Any]


def load_spec() -> dict[str, Any]:
    return json.loads(SPEC_PATH.read_text(encoding="utf-8"))


def tools_from_spec(spec: dict[str, Any]) -> list[ToolSpec]:
    tools = []
    for path, item in spec["paths"].items():
        for method in HTTP_METHODS:
            op = item.get(method)
            if op is None:
                continue
            params = [p for p in item.get("parameters", []) + op.get("parameters", [])
                      if p.get("in") == "path"]
            schema: dict[str, Any] = {
                "type": "object",
                "properties": {
                    p["name"]: {**p.get("schema", {"type": "string"}),
                                **({"description": p["description"]} if "description" in p else {})}
                    for p in params
                },
            }
            if params:
                schema["required"] = [p["name"] for p in params]
            description = "\n\n".join(x for x in (op.get("summary"), op.get("description")) if x)
            tools.append(ToolSpec(
                name=op["operationId"].rsplit(".", 1)[-1],
                description=description,
                method=method.upper(),
                path=path,
                path_params=tuple(p["name"] for p in params),
                input_schema=schema,
            ))
    return tools


def _error(text: str) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=True)


def build_mcp_server(spec: dict[str, Any], api_app: Any) -> Server:
    tools = {t.name: t for t in tools_from_spec(spec)}
    version = str(spec.get("info", {}).get("version", ""))

    async def list_tools(ctx: Any, params: Any) -> types.ListToolsResult:
        return types.ListToolsResult(tools=[
            types.Tool(name=t.name, description=t.description, input_schema=t.input_schema)
            for t in tools.values()
        ])

    async def call_tool(ctx: Any, params: types.CallToolRequestParams) -> types.CallToolResult:
        tool = tools.get(params.name)
        if tool is None:
            return _error(f"Unknown tool: {params.name}")
        args = params.arguments or {}
        missing = [p for p in tool.path_params if p not in args]
        if missing:
            return _error(f"Missing required argument(s): {', '.join(missing)}")
        path = tool.path
        for p in tool.path_params:
            path = path.replace("{" + p + "}", quote(str(args[p]), safe=""))
        transport = httpx.ASGITransport(app=api_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://sw-dev-agent.local") as client:
            response = await client.request(tool.method, path)
        if response.is_success:
            return types.CallToolResult(content=[types.TextContent(type="text", text=response.text)])
        return _error(f"HTTP {response.status_code}: {response.text}")

    return Server(SERVER_NAME, version=version, on_list_tools=list_tools, on_call_tool=call_tool)


def _default_server(catalog: SkillCatalog | None, info: BuildInfo | None) -> Server:
    api_app = create_app(catalog or SkillCatalog(default_skills_root()), info or BuildInfo.current())
    return build_mcp_server(load_spec(), api_app)


def create_http_app(host: str, catalog: SkillCatalog | None = None,
                    info: BuildInfo | None = None) -> Starlette:
    """Streamable HTTP MCP endpoint at MCP_PATH (R-MCP-004)."""
    return _default_server(catalog, info).streamable_http_app(streamable_http_path=MCP_PATH, host=host)


def run_stdio(catalog: SkillCatalog | None = None,
              info: BuildInfo | None = None) -> None:  # pragma: no cover - blocking stdio, covered by e2e
    """MCP over stdin/stdout (R-MCP-005)."""
    mcp_server = _default_server(catalog, info)

    async def main() -> None:
        async with stdio_server() as (read_stream, write_stream):
            await mcp_server.run(read_stream, write_stream, mcp_server.create_initialization_options())

    anyio.run(main)
