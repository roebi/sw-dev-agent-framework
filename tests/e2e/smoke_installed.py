"""
End-to-end smoke test against an INSTALLED sw-dev-agent (R-CI-007).

Run with the Python of a clean environment that has the built wheel
installed (with the [mcp] extra), outside the repository:

    python -I tests/e2e/smoke_installed.py

Starts the real `sw-dev-agent serve` and `sw-dev-agent mcp` processes and
fetches the orchestrator and all five sub-skills over HTTP, MCP streamable
HTTP and MCP stdio. Exits non-zero on the first failure.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess  # nosec B404 - starts the installed CLI under test
import sys
import time
import urllib.request

import anyio

SUB_SKILLS = [
    "gather-requirements-en",
    "design-architecture-en",
    "apply-tdd-loop-en",
    "code-review-en",
    "release-sw-project-en",
]
URL_RE = re.compile(r"(http://127\.0\.0\.1:\d+\S*)")


def start(args: list[str]) -> tuple[subprocess.Popen, str]:
    exe = shutil.which("sw-dev-agent")
    assert exe, "sw-dev-agent not on PATH"
    proc = subprocess.Popen(  # nosec B603 - fixed args
        [exe, *args], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    deadline = time.time() + 30
    while time.time() < deadline:
        line = proc.stdout.readline()
        m = URL_RE.search(line)
        if m:
            return proc, m.group(1)
    proc.kill()
    raise AssertionError("no URL printed on startup")


def get(url: str) -> tuple[int, str, str]:
    for _ in range(50):
        try:
            with urllib.request.urlopen(url, timeout=5) as r:  # nosec B310 - localhost only
                return r.status, r.headers["Content-Type"], r.read().decode("utf-8")
        except ConnectionError:
            time.sleep(0.1)
    raise AssertionError(f"cannot reach {url}")


def check_http() -> None:
    proc, base = start(["serve", "--port", "0"])
    try:
        status, ctype, body = get(f"{base}/health")
        assert status == 200 and json.loads(body) == {"status": "ok"}
        listed = {s["name"] for s in json.loads(get(f"{base}/skills")[2])["skills"]}
        assert listed == {"orchestrate-sw-dev-en", *SUB_SKILLS}, listed
        status, ctype, orch = get(f"{base}/skills/orchestrator")
        assert ctype == "text/markdown; charset=utf-8", ctype
        assert "name: orchestrate-sw-dev-en" in orch
        for name in SUB_SKILLS:
            assert name in orch, f"orchestrator does not reference {name}"
            body = get(f"{base}/skills/{name}")[2]
            assert f"name: {name}" in body
        version = json.loads(get(f"{base}/version")[2])
        assert version["skills_commit"] != "unknown", version
        print("HTTP ok:", version)
    finally:
        proc.terminate()
        proc.wait(10)


async def check_mcp_client(client) -> None:
    tools = {t.name for t in (await client.list_tools()).tools}
    assert tools == {"get_health", "get_version", "list_skills",
                     "get_orchestrator_skill", "get_skill"}, tools
    orch = await client.call_tool("get_orchestrator_skill", {})
    assert "name: orchestrate-sw-dev-en" in orch.content[0].text
    for name in SUB_SKILLS:
        r = await client.call_tool("get_skill", {"name": name})
        assert not r.is_error and f"name: {name}" in r.content[0].text


def check_mcp_http() -> None:
    from mcp import Client

    proc, url = start(["mcp", "--port", "0"])
    try:
        async def main():
            async with Client(url) as client:
                await check_mcp_client(client)
        anyio.run(main)
        print("MCP streamable HTTP ok:", url)
    finally:
        proc.terminate()
        proc.wait(10)


def check_mcp_stdio() -> None:
    from mcp import Client, StdioServerParameters

    params = StdioServerParameters(command=shutil.which("sw-dev-agent"), args=["mcp", "--stdio"])

    async def main():
        async with Client(params) as client:
            await check_mcp_client(client)
    anyio.run(main)
    print("MCP stdio ok")


if __name__ == "__main__":
    check_http()
    if "--no-mcp" not in sys.argv:
        check_mcp_http()
        check_mcp_stdio()
    print("E2E OK")
