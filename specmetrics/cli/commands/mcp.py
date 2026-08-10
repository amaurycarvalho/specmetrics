"""CLI commands for managing the SpecMetrics MCP server."""

from __future__ import annotations

import asyncio
import os
import signal
import time
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

import typer

if TYPE_CHECKING:
    from specmetrics.mcp.server import (
        MCPServer,
        ServerConfiguration,
        TransportType,
    )

mcp_cli = typer.Typer(name="mcp", help="Manage the SpecMetrics MCP server")

PID_FILE = Path("/tmp/specmetrics-mcp.pid")


def _load_mcp_server() -> tuple[type[MCPServer], type[ServerConfiguration], type[TransportType]]:
    """Import the heavy MCP server module lazily to keep ``cli.app`` cheap."""
    from specmetrics.mcp.server import MCPServer, ServerConfiguration, TransportType

    return MCPServer, ServerConfiguration, TransportType


def _read_pid() -> int | None:
    """Read the stored MCP server PID, or return None when unavailable."""
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def _write_pid(pid: int) -> None:
    """Persist the MCP server PID to the PID file."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(pid))


def _remove_pid() -> None:
    """Remove the MCP server PID file if present."""
    PID_FILE.unlink(missing_ok=True)


@mcp_cli.command()
def start(
    host: Annotated[
        str | None,
        typer.Option("--host", help="Network interface to bind"),
    ] = None,
    port: Annotated[
        int | None,
        typer.Option("--port", help="TCP port to listen on"),
    ] = None,
    transport: Annotated[
        str | None,
        typer.Option("--transport", help="Transport protocol: stdio or sse"),
    ] = None,
    max_connections: Annotated[
        int | None,
        typer.Option("--max-connections", help="Maximum concurrent connections"),
    ] = None,
    log_level: Annotated[
        str | None,
        typer.Option("--log-level", help="Logging verbosity"),
    ] = None,
    config_file: Annotated[
        str,
        typer.Option("--config", "-c", help="Path to configuration file"),
    ] = "specmetrics.yml",
) -> None:
    """Start the MCP server."""
    MCPServer, ServerConfiguration, TransportType = _load_mcp_server()
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
    timeout: Annotated[
        int,
        typer.Option("--timeout", help="Seconds to wait for graceful shutdown"),
    ] = 10,
) -> None:
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
def status() -> None:
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
