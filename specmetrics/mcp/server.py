"""MCP server implementation for SpecMetrics."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import ClassVar, Self

import structlog
from mcp.server import Server as MCPServerInstance
from pydantic import BaseModel, Field

from specmetrics.mcp.registry import PromptRegistry, ResourceRegistry, ToolRegistry
from specmetrics.mcp.transport import SSETransport, StdioTransport

from ._handlers import (
    attach_handlers,
    refresh_capabilities,
    register_prompts,
    register_resources,
    register_tools,
)
from ._params import check_param_schemas, check_required_params
from ._support import (
    LogLevel,
    MCPConnection,
    ServerState,
    ServerStatus,
    ToolError,
    ToolRequest,
    TransportType,
)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
logger = structlog.get_logger(__name__)

__all__ = [
    "LogLevel",
    "MCPConnection",
    "MCPServer",
    "ServerConfiguration",
    "ServerState",
    "ServerStatus",
    "ToolError",
    "ToolRequest",
    "TransportType",
]


class ServerConfiguration(BaseModel):
    """Configuration for the MCP server."""

    host: str = Field(
        default="127.0.0.1", description="Network interface to bind (SSE mode)"
    )
    port: int = Field(
        default=8100, description="TCP port to listen on (SSE mode)", ge=1024, le=65535
    )
    transport: TransportType = Field(
        default=TransportType.stdio, description="Transport protocol"
    )
    max_connections: int = Field(
        default=10, description="Maximum concurrent client connections", ge=1
    )
    log_level: LogLevel = Field(default=LogLevel.info, description="Logging verbosity")
    pipeline_timeout_seconds: int = Field(
        default=120, description="Max wait time for pipeline tool execution", ge=30
    )
    shutdown_timeout_seconds: int = Field(
        default=10, description="Max wait for in-flight requests on shutdown", ge=1
    )

    @classmethod
    def from_yaml(
        cls: type[Self], path: str | Path, overrides: dict | None = None
    ) -> ServerConfiguration:
        """Build a configuration from a YAML file and optional overrides."""
        import yaml

        path = Path(path)
        if not path.exists():
            return cls(**(overrides or {}))
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        mcp_config = data.get("mcp", {})
        if overrides:
            mcp_config.update(overrides)
        return cls(**mcp_config)


class MCPServer:
    """MCP server that exposes SpecMetrics tools, resources, and prompts."""

    SUPPORTED_PROTOCOL_VERSIONS: ClassVar[frozenset[str]] = frozenset({"2025-03-26"})

    def __init__(self: Self, config: ServerConfiguration | None = None) -> None:
        """Initialize the server with its configuration and empty registries."""
        self.config = config or ServerConfiguration()
        self.tool_registry = ToolRegistry()
        self.resource_registry = ResourceRegistry()
        self.prompt_registry = PromptRegistry()
        self.status = ServerStatus(self.config)
        self.connections: dict[str, MCPConnection] = {}
        self._mcp_server: MCPServerInstance | None = None
        self._shutdown_event = asyncio.Event()
        self._active_requests: int = 0
        self._setup_logging()

    def _setup_logging(self: Self) -> None:
        """Configure structlog based on the configured log level."""
        level = getattr(logging, self.config.log_level.value.upper(), logging.INFO)
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(level),
        )

    def _check_protocol_version(self: Self, version: str) -> bool:
        """Return whether a protocol version is supported."""
        return version in self.SUPPORTED_PROTOCOL_VERSIONS

    def _validate_tool_params(self: Self, tool_name: str, params: dict) -> None:
        """Validate tool parameters against the tool's input schema."""
        tool_def = self.tool_registry.get_tool(tool_name)
        if tool_def is None:
            raise ToolError(-32601, f"Unknown tool: {tool_name}")

        schema = tool_def.inputSchema
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        check_required_params(required, params, properties)
        check_param_schemas(params, properties)

    def _register_connection(
        self: Self, transport_type: TransportType, protocol_version: str
    ) -> MCPConnection | None:
        """Register a new connection if capacity allows, else return None."""
        if len(self.connections) >= self.config.max_connections:
            logger.warning(
                "max_connections_reached", max_connections=self.config.max_connections
            )
            return None
        conn = MCPConnection(transport_type, protocol_version)
        self.connections[conn.connection_id] = conn
        self.status.active_connections = len(self.connections)
        return conn

    def _remove_connection(self: Self, connection_id: str) -> None:
        """Remove a connection and update the active connection count."""
        self.connections.pop(connection_id, None)
        self.status.active_connections = len(self.connections)

    async def start(self: Self) -> None:
        """Start the MCP server and run the configured transport."""
        self.status.state = ServerState.starting
        logger.info(
            "mcp_server_starting",
            transport=self.config.transport.value,
            host=self.config.host,
            port=self.config.port,
        )

        self._mcp_server = MCPServerInstance("specmetrics")
        self.refresh_capabilities()
        self._attach_handlers()

        if self.config.transport == TransportType.stdio:
            transport = StdioTransport(self._mcp_server)
            self.status.start()
            await transport.run()
        elif self.config.transport == TransportType.sse:
            transport = SSETransport(
                self._mcp_server, self.config.host, self.config.port
            )
            self.status.start()
            await transport.run()

    async def stop(self: Self) -> None:
        """Stop the MCP server, waiting for in-flight requests to drain."""
        self.status.state = ServerState.stopping
        logger.info(
            "mcp_server_stopping",
            active_requests=self._active_requests,
            shutdown_timeout=self.config.shutdown_timeout_seconds,
        )

        if self._active_requests > 0:
            waited = 0
            while waited < self.config.shutdown_timeout_seconds:
                await asyncio.sleep(0.5)
                waited += 0.5
                if self._active_requests == 0:
                    logger.info("mcp_server_in_flight_requests_completed")
                    break
            else:
                logger.warning(
                    "mcp_server_shutdown_timeout",
                    remaining_requests=self._active_requests,
                )

        self.status.stop()

    def refresh_capabilities(self: Self) -> None:
        """Re-discover and register all tools, resources, and prompts."""
        refresh_capabilities(self)

    def _register_tools(self: Self) -> None:
        """Register all MCP tools and their handlers."""
        register_tools(self)

    def _register_resources(self: Self) -> None:
        """Register all MCP resource templates and their handlers."""
        register_resources(self)

    def _register_prompts(self: Self) -> None:
        """Register all MCP prompts."""
        register_prompts(self)

    def _track_request(self: Self) -> None:
        """Increment the in-flight request counter."""
        self._active_requests += 1

    def _finish_request(self: Self) -> None:
        """Decrement the in-flight request counter."""
        self._active_requests = max(0, self._active_requests - 1)

    def _attach_handlers(self: Self) -> None:
        """Attach the MCP server request handlers."""
        attach_handlers(self)


def main() -> None:
    """Standalone entry point for the MCP server.

    Reads configuration from ``specmetrics.yml`` (or uses defaults)
    and runs the server until interrupted.
    """
    import argparse

    parser = argparse.ArgumentParser(description="SpecMetrics MCP Server")
    parser.add_argument(
        "--config", default="specmetrics.yml", help="Path to configuration file"
    )
    parser.add_argument(
        "--host", default=None, help="Network interface to bind (SSE mode)"
    )
    parser.add_argument("--port", type=int, default=None, help="TCP port (SSE mode)")
    parser.add_argument(
        "--transport", default=None, choices=["stdio", "sse"], help="Transport protocol"
    )
    parser.add_argument("--log-level", default=None, help="Logging verbosity")
    args = parser.parse_args()

    overrides = {
        k: v
        for k, v in {
            "host": args.host,
            "port": args.port,
            "transport": TransportType(args.transport) if args.transport else None,
            "log_level": args.log_level,
        }.items()
        if v is not None
    }

    config = ServerConfiguration.from_yaml(args.config, overrides)
    server = MCPServer(config)

    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        logger.info("mcp_server_interrupted")
