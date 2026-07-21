from __future__ import annotations

import asyncio
import os
import signal
import time
from pathlib import Path

import typer

from specmetrics.mcp.server import MCPServer, ServerConfiguration, TransportType

mcp_cli = typer.Typer(name="mcp", help="Manage the SpecMetrics MCP server")

PID_FILE = Path("/tmp/specmetrics-mcp.pid")


def _read_pid() -> int | None:
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def _write_pid(pid: int) -> None:
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def _remove_pid() -> None:
    PID_FILE.unlink(missing_ok=True)


@mcp_cli.command()
def start(
    host: str = typer.Option(None, "--host", help="Network interface to bind"),
    port: int = typer.Option(None, "--port", help="TCP port to listen on"),
    transport: str = typer.Option(
        None, "--transport", help="Transport protocol: stdio or sse"
    ),
    max_connections: int = typer.Option(
        None, "--max-connections", help="Maximum concurrent connections"
    ),
    log_level: str = typer.Option(None, "--log-level", help="Logging verbosity"),
    config_file: str = typer.Option(
        "specmetrics.yml", "--config", "-c", help="Path to configuration file"
    ),
):
    """Start the MCP server."""
    overrides = {
        k: v
        for k, v in {
            "host": host,
            "port": port,
            "transport": TransportType(transport) if transport else None,
            "max_connections": max_connections,
            "log_level": log_level,
        }.items()
        if v is not None
    }
    config = ServerConfiguration.from_yaml(config_file, overrides)

    server = MCPServer(config)
    _write_pid(os.getpid())

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        pass
    finally:
        _remove_pid()
        typer.echo("MCP server stopped.")


@mcp_cli.command()
def stop(
    timeout: int = typer.Option(
        10, "--timeout", help="Seconds to wait for graceful shutdown"
    ),
):
    """Stop the MCP server."""
    pid = _read_pid()
    if pid is None:
        typer.echo("No running MCP server found.", err=True)
        raise typer.Exit(1)

    try:
        os.kill(pid, signal.SIGTERM)
    except ProcessLookupError:
        typer.echo("MCP server process not found. Removing stale PID file.")
        _remove_pid()
        raise typer.Exit(1)

    waited = 0
    while waited < timeout:
        try:
            os.kill(pid, 0)
            time.sleep(0.5)
            waited += 0.5
        except ProcessLookupError:
            _remove_pid()
            typer.echo("MCP server stopped gracefully.")
            return

    typer.echo(f"Server did not stop after {timeout}s. Sending SIGKILL.")
    try:
        os.kill(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    _remove_pid()


@mcp_cli.command()
def status():
    """Show MCP server status."""
    pid = _read_pid()
    if pid is None:
        typer.echo("MCP server: stopped")
        return

    try:
        os.kill(pid, 0)
        typer.echo(f"MCP server: running (PID {pid})")
    except ProcessLookupError:
        _remove_pid()
        typer.echo("MCP server: stopped (stale PID file cleaned)")
