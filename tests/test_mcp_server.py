"""TDD - MCP adapter over the OpenAPI spec (R-MCP-001..005)."""
import copy
import json
from pathlib import Path

import anyio
import pytest
from mcp import Client
from starlette.testclient import TestClient

from sw_dev_agent.api import SPEC_PATH, BuildInfo, create_app
from sw_dev_agent.catalog import ORCHESTRATOR, SkillCatalog
from sw_dev_agent.mcp_server import (
    build_mcp_server,
    create_http_app,
    tools_from_spec,
)
from sw_dev_agent.server import MCP_PATH

SPEC = json.loads(SPEC_PATH.read_text())
INFO = BuildInfo(package_version="9.9.9", skills_commit="abc123")


@pytest.fixture
def root(tmp_path: Path) -> Path:
    for name in (ORCHESTRATOR, "gather-requirements-en"):
        (tmp_path / name).mkdir()
        (tmp_path / name / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: Desc {name}.\n---\n# {name}\n", encoding="utf-8"
        )
    return tmp_path


@pytest.fixture
def api(root):
    return create_app(SkillCatalog(root), INFO)


def run(coro_fn):
    return anyio.run(coro_fn)


class TestToolsFromSpec:
    def test_one_tool_per_operation(self):
        names = [t.name for t in tools_from_spec(SPEC)]
        assert sorted(names) == sorted(
            ["get_health", "get_version", "list_skills", "get_orchestrator_skill", "get_skill"]
        )

    def test_path_parameter_becomes_required_input(self):
        tool = next(t for t in tools_from_spec(SPEC) if t.name == "get_skill")
        assert tool.input_schema["required"] == ["name"]
        assert tool.input_schema["properties"]["name"]["pattern"] == "^[a-z0-9]+(-[a-z0-9]+)*$"
        assert tool.method == "GET" and tool.path == "/skills/{name}"

    def test_tool_without_params_has_empty_object_schema(self):
        tool = next(t for t in tools_from_spec(SPEC) if t.name == "list_skills")
        assert tool.input_schema == {"type": "object", "properties": {}}

    def test_description_from_spec(self):
        tool = next(t for t in tools_from_spec(SPEC) if t.name == "get_orchestrator_skill")
        assert "orchestrate-sw-dev-en" in tool.description

    def test_new_spec_operation_becomes_new_tool(self):
        spec = copy.deepcopy(SPEC)
        spec["paths"]["/extra"] = {"get": {"operationId": "x.y.get_extra", "summary": "Extra",
                                           "responses": {"200": {"description": "ok"}}}}
        assert "get_extra" in [t.name for t in tools_from_spec(spec)]


class TestMcpServerInProcess:
    def test_list_tools_matches_spec(self, api):
        async def main():
            async with Client(build_mcp_server(SPEC, api)) as client:
                return await client.list_tools()

        names = {t.name for t in run(main).tools}
        assert names == {t.name for t in tools_from_spec(SPEC)}

    @pytest.mark.parametrize(
        ("tool", "args", "path"),
        [
            ("list_skills", {}, "/skills"),
            ("get_orchestrator_skill", {}, "/skills/orchestrator"),
            ("get_skill", {"name": "gather-requirements-en"}, "/skills/gather-requirements-en"),
            ("get_health", {}, "/health"),
            ("get_version", {}, "/version"),
        ],
    )
    def test_tool_returns_same_content_as_http(self, api, tool, args, path):
        async def main():
            async with Client(build_mcp_server(SPEC, api)) as client:
                return await client.call_tool(tool, args)

        result = run(main)
        with api.test_client() as http:
            expected = http.get(path).text
        assert not result.is_error
        assert result.content[0].text == expected

    def test_unknown_skill_is_error_result(self, api):
        async def main():
            async with Client(build_mcp_server(SPEC, api)) as client:
                return await client.call_tool("get_skill", {"name": "missing-skill"})

        result = run(main)
        assert result.is_error
        assert "404" in result.content[0].text

    def test_unknown_tool_is_error_result(self, api):
        async def main():
            async with Client(build_mcp_server(SPEC, api)) as client:
                return await client.call_tool("no_such_tool", {})

        assert run(main).is_error

    def test_path_argument_is_url_encoded(self, api):
        async def main():
            async with Client(build_mcp_server(SPEC, api)) as client:
                return await client.call_tool("get_skill", {"name": "../../pyproject.toml"})

        result = run(main)
        assert result.is_error
        assert "[project]" not in result.content[0].text


class TestHttpApp:
    def test_mcp_endpoint_is_mounted(self, root):
        app = create_http_app("127.0.0.1", catalog=SkillCatalog(root), info=INFO)
        with TestClient(app, base_url="http://127.0.0.1:8765") as c:
            r = c.post(
                MCP_PATH,
                headers={"Accept": "application/json, text/event-stream",
                         "Content-Type": "application/json"},
                json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
                    "protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "t", "version": "1"}}},
            )
        assert r.status_code == 200
        assert "sw-dev-agent-framework" in r.text
