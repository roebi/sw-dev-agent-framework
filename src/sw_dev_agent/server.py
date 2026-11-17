"""
Server start helpers - port resolution, socket binding, uvicorn runner.

The socket is bound before uvicorn starts, so port 0 yields the real port
and "port in use" is reported cleanly (R-CLI-002..006).
"""
from __future__ import annotations

import errno
import socket
from types import ModuleType
from typing import Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765
PORT_ENV = "SW_DEV_AGENT_PORT"
MCP_PATH = "/sw-dev-agent-framework/mcp"
MCP_INSTALL_HINT = 'uv tool install "sw-dev-agent-framework[mcp]"'


class PortInUse(OSError):
    """The requested port is already in use."""


def resolve_port(flag: int | None, env: str | None) -> int:
    """Flag wins over env, env wins over the default."""
    if flag is not None:
        port = flag
    elif env is not None:
        try:
            port = int(env)
        except ValueError:
            raise ValueError(f"{PORT_ENV} must be an integer, got '{env}'") from None
    else:
        port = DEFAULT_PORT
    if not 0 <= port <= 65535:
        raise ValueError(f"port must be between 0 and 65535, got {port}")
    return port


def bind_socket(host: str, port: int) -> socket.socket:
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
    except OSError as exc:
        sock.close()
        if exc.errno == errno.EADDRINUSE:
            raise PortInUse(f"port {port} on {host} is already in use") from None
        raise
    sock.listen(128)
    return sock


def base_url(host: str, port: int) -> str:
    shown = f"[{host}]" if ":" in host else host
    return f"http://{shown}:{port}"


def run_uvicorn(asgi_app: Any, sock: socket.socket) -> None:  # pragma: no cover - blocking I/O, covered by e2e
    import uvicorn

    config = uvicorn.Config(asgi_app, log_level="info")
    uvicorn.Server(config).run(sockets=[sock])


def load_mcp_module() -> ModuleType:
    from sw_dev_agent import mcp_server

    return mcp_server
