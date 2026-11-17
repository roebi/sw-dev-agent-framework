"""TDD - server start helpers and CLI serve/mcp commands (R-CLI-001..007, R-MCP-006)."""
import socket

import pytest
from typer.testing import CliRunner

from sw_dev_agent import server
from sw_dev_agent.cli import app
from sw_dev_agent.server import (
    DEFAULT_HOST,
    DEFAULT_PORT,
    PortInUse,
    bind_socket,
    resolve_port,
)

runner = CliRunner()


class TestResolvePort:
    def test_default(self):
        assert resolve_port(None, None) == DEFAULT_PORT == 8765

    def test_env(self):
        assert resolve_port(None, "9000") == 9000

    def test_flag_wins_over_env(self):
        assert resolve_port(9100, "9000") == 9100

    def test_zero_allowed(self):
        assert resolve_port(0, None) == 0

    @pytest.mark.parametrize("bad", ["abc", "-1", "70000"])
    def test_invalid_env_raises(self, bad):
        with pytest.raises(ValueError):
            resolve_port(None, bad)

    def test_default_host_is_loopback(self):
        assert DEFAULT_HOST == "127.0.0.1"


class TestBindSocket:
    def test_port_zero_picks_free_port(self):
        sock = bind_socket("127.0.0.1", 0)
        try:
            assert sock.getsockname()[1] > 0
        finally:
            sock.close()

    def test_port_in_use_raises(self):
        busy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        try:
            with pytest.raises(PortInUse):
                bind_socket("127.0.0.1", busy.getsockname()[1])
        finally:
            busy.close()

    def test_base_url(self):
        assert server.base_url("127.0.0.1", 8765) == "http://127.0.0.1:8765"
        assert server.base_url("::1", 8765) == "http://[::1]:8765"


@pytest.fixture
def fake_run(monkeypatch):
    calls = []

    def run(asgi_app, sock):
        calls.append((asgi_app, sock.getsockname()))
        sock.close()

    monkeypatch.setattr(server, "run_uvicorn", run)
    return calls


class TestServeCommand:
    def test_serve_prints_url_and_runs(self, fake_run, monkeypatch):
        monkeypatch.delenv("SW_DEV_AGENT_PORT", raising=False)
        result = runner.invoke(app, ["serve", "--port", "0"])
        assert result.exit_code == 0, result.output
        port = fake_run[0][1][1]
        assert f"http://127.0.0.1:{port}" in result.output
        assert fake_run[0][1][0] == "127.0.0.1"

    def test_serve_uses_env_port(self, fake_run, monkeypatch):
        probe = bind_socket("127.0.0.1", 0)
        port = probe.getsockname()[1]
        probe.close()
        monkeypatch.setenv("SW_DEV_AGENT_PORT", str(port))
        result = runner.invoke(app, ["serve"])
        assert result.exit_code == 0, result.output
        assert fake_run[0][1][1] == port

    def test_serve_port_in_use_exits_1(self, fake_run):
        busy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        try:
            result = runner.invoke(app, ["serve", "--port", str(busy.getsockname()[1])])
        finally:
            busy.close()
        assert result.exit_code == 1
        assert "already in use" in result.output
        assert "Traceback" not in result.output
        assert fake_run == []

    def test_serve_invalid_env_port_exits_1(self, fake_run, monkeypatch):
        monkeypatch.setenv("SW_DEV_AGENT_PORT", "abc")
        result = runner.invoke(app, ["serve"])
        assert result.exit_code == 1
        assert "SW_DEV_AGENT_PORT" in result.output


class TestMcpCommandWithoutExtra:
    def test_missing_extra_exits_1_with_hint(self, monkeypatch):
        def missing():
            raise ImportError("No module named 'mcp'")

        monkeypatch.setattr(server, "load_mcp_module", missing)
        result = runner.invoke(app, ["mcp", "--port", "0"])
        assert result.exit_code == 1
        assert "sw-dev-agent-framework[mcp]" in result.output


class TestExistingCommandsUnchanged:
    def test_phases_still_works(self):
        result = runner.invoke(app, ["phases"])
        assert result.exit_code == 0
        assert "gather-requirements-en" in result.output

    def test_help_lists_all_commands(self):
        result = runner.invoke(app, ["--help"])
        for cmd in ("start", "status", "phases", "serve", "mcp"):
            assert cmd in result.output


class TestHelpText:
    """Bugfix: Rich markup swallowed '[mcp]' in the help text of 'mcp'."""

    def test_main_help_shows_mcp_extra(self):
        result = runner.invoke(app, ["--help"], env={"COLUMNS": "200"})
        assert "requires the [mcp] extra" in result.output

    def test_mcp_help_shows_mcp_extra(self):
        result = runner.invoke(app, ["mcp", "--help"], env={"COLUMNS": "200"})
        assert "requires the [mcp] extra" in result.output
