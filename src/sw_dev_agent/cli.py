"""
sw-dev-agent CLI - Orchestrate software development via TDD-driven skill pipeline.
"""
import os
import socket

import typer
from rich.console import Console
from rich.table import Table

from sw_dev_agent import server
from sw_dev_agent.orchestrator import PHASE_SKILL_MAP, Orchestrator
from sw_dev_agent.phases import Phase

app = typer.Typer(
    name="sw-dev-agent",
    help="Agentic SW development framework. Runs REQUIREMENTS -> DESIGN -> IMPLEMENT -> REVIEW -> RELEASE.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def start(
    goal: str = typer.Argument(..., help="One-sentence goal for the software project."),
) -> None:
    """Start a new SW development pipeline from a goal statement."""
    orch = Orchestrator(goal=goal)
    console.print("\n[bold green]SW Dev Agent[/bold green] - pipeline started")
    console.print(f"Goal: [italic]{goal}[/italic]\n")
    _print_pipeline_status(orch)
    console.print(f"\nActive skill: [bold cyan]{orch.active_skill()}[/bold cyan]")
    console.print("\nHandover state written to: [dim]Handover-State.md[/dim]")
    _write_handover(orch)


@app.command()
def status() -> None:
    """Show the current pipeline status from Handover-State.md."""
    import os
    if not os.path.exists("Handover-State.md"):
        console.print("[red]No Handover-State.md found. Run 'sw-dev-agent start <goal>' first.[/red]")
        raise typer.Exit(1)
    from sw_dev_agent.orchestrator import HandoverState
    with open("Handover-State.md") as f:
        state_yaml = f.read()
    state = HandoverState.from_yaml(state_yaml)
    orch = Orchestrator(goal=state.goal)
    orch.state = state
    _print_pipeline_status(orch)
    if not orch.is_done():
        console.print(f"\nActive skill: [bold cyan]{orch.active_skill()}[/bold cyan]")
    else:
        console.print("\n[bold green]Pipeline complete - project released.[/bold green]")


@app.command()
def phases() -> None:
    """List all SW dev phases and their mapped skills."""
    table = Table(title="SW Dev Pipeline Phases")
    table.add_column("Order", style="dim")
    table.add_column("Phase", style="bold")
    table.add_column("Skill", style="cyan")
    for i, phase in enumerate(Phase.ordered(), 1):
        table.add_row(str(i), phase.value, PHASE_SKILL_MAP[phase])
    console.print(table)


HOST_OPTION = typer.Option(server.DEFAULT_HOST, help="Interface to bind. Default: loopback only.")
PORT_OPTION = typer.Option(
    None,
    help=f"Port to listen on (0 = free port). Default: ${server.PORT_ENV} or {server.DEFAULT_PORT}.",
)


@app.command()
def serve(host: str = HOST_OPTION, port: int | None = PORT_OPTION) -> None:
    """Serve the bundled skills over a local OpenAPI HTTP API."""
    from sw_dev_agent.api import BuildInfo, create_app
    from sw_dev_agent.catalog import SkillCatalog, default_skills_root

    sock = _bind_or_exit(host, port)
    url = server.base_url(host, sock.getsockname()[1])
    typer.echo(f"sw-dev-agent skills API: {url}")
    typer.echo(f"Start here: {url}/skills/orchestrator  (OpenAPI: {url}/openapi.json)")
    server.run_uvicorn(create_app(SkillCatalog(default_skills_root()), BuildInfo.current()), sock)


@app.command()
def mcp(
    host: str = HOST_OPTION,
    port: int | None = PORT_OPTION,
    stdio: bool = typer.Option(False, "--stdio", help="Serve MCP over stdin/stdout instead of HTTP."),
) -> None:
    """Serve the skills API as MCP tools (requires the \\[mcp] extra)."""
    try:
        mcp_module = server.load_mcp_module()
    except ImportError:
        typer.echo(f"MCP support is not installed. Install it with: {server.MCP_INSTALL_HINT}", err=True)
        raise typer.Exit(1) from None
    if stdio:
        mcp_module.run_stdio()
        return
    sock = _bind_or_exit(host, port)
    url = server.base_url(host, sock.getsockname()[1]) + server.MCP_PATH
    typer.echo(f"sw-dev-agent MCP server (streamable HTTP): {url}")
    server.run_uvicorn(mcp_module.create_http_app(host), sock)


def _bind_or_exit(host: str, port: int | None) -> socket.socket:
    try:
        resolved = server.resolve_port(port, os.environ.get(server.PORT_ENV))
        return server.bind_socket(host, resolved)
    except (ValueError, OSError) as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1) from None


def _print_pipeline_status(orch: Orchestrator) -> None:
    table = Table(title=f"Pipeline: {orch.goal[:60]}")
    table.add_column("Phase")
    table.add_column("Skill")
    table.add_column("Status")
    done_phases = {r.phase for r in orch.state.results if r.is_done()}
    for phase in Phase.ordered():
        is_current = phase == orch.state.current_phase and not orch.is_done()
        status = "done" if phase in done_phases else ("active" if is_current else "pending")
        style = "green" if status == "done" else ("yellow" if status == "active" else "dim")
        table.add_row(phase.value, PHASE_SKILL_MAP[phase], f"[{style}]{status}[/{style}]")
    console.print(table)


def _write_handover(orch: Orchestrator) -> None:
    with open("Handover-State.md", "w") as f:
        f.write(orch.state.to_yaml())


if __name__ == "__main__":
    app()
