from __future__ import annotations

import asyncio
import json
import logging
import time
import uuid
from enum import Enum
from pathlib import Path

import structlog
from mcp.server import Server as MCPServerInstance
from mcp.types import TextContent
from pydantic import BaseModel, Field

from specmetrics.mcp.registry import PromptRegistry, ResourceRegistry, ToolRegistry
from specmetrics.mcp.transport import SSETransport, StdioTransport

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
logger = structlog.get_logger(__name__)


class ServerState(str, Enum):
    stopped = "stopped"
    starting = "starting"
    running = "running"
    stopping = "stopping"
    error = "error"


class TransportType(str, Enum):
    stdio = "stdio"
    sse = "sse"


class LogLevel(str, Enum):
    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"


class ServerConfiguration(BaseModel):
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
        cls, path: str | Path, overrides: dict | None = None
    ) -> ServerConfiguration:
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


class MCPConnection:
    def __init__(self, transport_type: TransportType, protocol_version: str):
        self.connection_id: str = uuid.uuid4().hex[:12]
        self.transport_type: TransportType = transport_type
        self.protocol_version: str = protocol_version
        self.connected_at: float = time.time()
        self.last_activity_at: float = time.time()
        self.active_request_id: str | None = None

    def touch(self) -> None:
        self.last_activity_at = time.time()


class ServerStatus:
    def __init__(self, config: ServerConfiguration):
        self.state: ServerState = ServerState.stopped
        self.uptime_seconds: float = 0.0
        self.active_connections: int = 0
        self.max_connections: int = config.max_connections
        self.total_requests_handled: int = 0
        self.total_errors: int = 0
        self.last_error_timestamp: float | None = None
        self.transport: TransportType = config.transport
        self.version: str = "2025-03-26"
        self._start_time: float = 0.0

    def start(self) -> None:
        self.state = ServerState.running
        self._start_time = time.time()

    def stop(self) -> None:
        self.state = ServerState.stopped

    def record_request(self) -> None:
        self.total_requests_handled += 1

    def record_error(self) -> None:
        self.total_errors += 1
        self.last_error_timestamp = time.time()

    @property
    def uptime(self) -> float:
        if self.state == ServerState.running:
            return time.time() - self._start_time
        return self.uptime_seconds


class ToolRequest:
    def __init__(
        self, request_id: str, tool_name: str, parameters: dict, connection_id: str
    ):
        self.request_id: str = request_id
        self.tool_name: str = tool_name
        self.parameters: dict = parameters
        self.received_at: float = time.time()
        self.connection_id: str = connection_id


class ToolError(Exception):
    def __init__(self, code: int, message: str, details: dict | None = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)


class MCPServer:
    SUPPORTED_PROTOCOL_VERSIONS = {"2025-03-26"}

    def __init__(self, config: ServerConfiguration | None = None):
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

    def _setup_logging(self) -> None:
        level = getattr(logging, self.config.log_level.value.upper(), logging.INFO)
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(level),
        )

    def _check_protocol_version(self, version: str) -> bool:
        return version in self.SUPPORTED_PROTOCOL_VERSIONS

    def _validate_tool_params(self, tool_name: str, params: dict) -> None:
        tool_def = self.tool_registry.get_tool(tool_name)
        if tool_def is None:
            raise ToolError(-32601, f"Unknown tool: {tool_name}")

        schema = tool_def.inputSchema
        required = schema.get("required", [])
        properties = schema.get("properties", {})

        for field in required:
            if field not in params or params[field] is None:
                raise ToolError(
                    -32602,
                    f"Missing required parameter: {field}",
                    {"field": field, "expected": properties.get(field, {})},
                )

        for field, value in params.items():
            if field not in properties:
                raise ToolError(
                    -32602,
                    f"Unknown parameter: {field}",
                    {"field": field, "valid_params": list(properties.keys())},
                )
            prop = properties[field]
            if "enum" in prop and value not in prop["enum"]:
                raise ToolError(
                    -32602,
                    f"Invalid value for {field}: {value}",
                    {"field": field, "value": value, "expected": prop["enum"]},
                )
            if prop.get("type") == "string" and not isinstance(value, str):
                raise ToolError(
                    -32602,
                    f"Invalid type for {field}: expected string, got {type(value).__name__}",
                    {
                        "field": field,
                        "expected_type": "string",
                        "received_type": type(value).__name__,
                    },
                )

    def _register_connection(
        self, transport_type: TransportType, protocol_version: str
    ) -> MCPConnection | None:
        if len(self.connections) >= self.config.max_connections:
            logger.warning(
                "max_connections_reached", max_connections=self.config.max_connections
            )
            return None
        conn = MCPConnection(transport_type, protocol_version)
        self.connections[conn.connection_id] = conn
        self.status.active_connections = len(self.connections)
        return conn

    def _remove_connection(self, connection_id: str) -> None:
        self.connections.pop(connection_id, None)
        self.status.active_connections = len(self.connections)

    async def start(self) -> None:
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

    async def stop(self) -> None:
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

    def refresh_capabilities(self) -> None:
        """Re-discover and register all tools, resources, and prompts.

        Called at startup to perform initial registration. May be called
        again at runtime to pick up newly installed plugins without a
        server restart (FR-012).  Currently registers statically defined
        capabilities; future versions may poll the Kernel capability
        registry for dynamic discovery.
        """
        self.tool_registry = ToolRegistry()
        self.resource_registry = ResourceRegistry()
        self.prompt_registry = PromptRegistry()
        self._register_tools()
        self._register_resources()
        self._register_prompts()
        logger.info(
            "mcp_capabilities_refreshed",
            tools=len(self.tool_registry.list_tools()),
            resources=len(self.resource_registry.list_templates()),
            prompts=len(self.prompt_registry.list_prompts()),
        )

    def _register_tools(self) -> None:
        from specmetrics.mcp.tools.explain import (
            EXPLAIN_COMPARE_TOOL,
            EXPLAIN_TOOL,
            handle_explain_compare,
            handle_explain_measurement,
        )
        from specmetrics.mcp.tools.export import (
            EXPORT_RESULTS_TOOL,
            handle_export_results,
        )
        from specmetrics.mcp.tools.measure import RUN_PIPELINE_TOOL, handle_run_pipeline
        from specmetrics.mcp.tools.specs import (
            LIST_SPECS_TOOL,
            READ_SPEC_TOOL,
            handle_list_specs,
            handle_read_spec,
        )
        from specmetrics.mcp.tools.status import GET_STATUS_TOOL

        self.tool_registry.register(EXPLAIN_TOOL, handle_explain_measurement)
        self.tool_registry.register(EXPLAIN_COMPARE_TOOL, handle_explain_compare)
        self.tool_registry.register(RUN_PIPELINE_TOOL, handle_run_pipeline)
        self.tool_registry.register(LIST_SPECS_TOOL, handle_list_specs)
        self.tool_registry.register(READ_SPEC_TOOL, handle_read_spec)
        self.tool_registry.register(EXPORT_RESULTS_TOOL, handle_export_results)
        self.tool_registry.register(
            GET_STATUS_TOOL,
            lambda params: [
                TextContent(
                    type="text",
                    text=json.dumps(
                        {
                            "state": self.status.state.value,
                            "uptime_seconds": self.status.uptime,
                            "active_connections": self.status.active_connections,
                            "max_connections": self.status.max_connections,
                            "total_requests_handled": self.status.total_requests_handled,
                            "total_errors": self.status.total_errors,
                            "transport": self.status.transport.value,
                            "version": self.status.version,
                        },
                        indent=2,
                    ),
                )
            ],
        )

    def _register_resources(self) -> None:
        from specmetrics.mcp.resources.specs import (
            SPEC_RESOURCE_TEMPLATE,
            handle_spec_resource,
        )
        from specmetrics.mcp.resources.measurements import (
            MEASUREMENT_RESOURCE_TEMPLATE,
            EVIDENCE_RESOURCE_TEMPLATE,
            EXPORT_RESOURCE_TEMPLATE,
            handle_measurement_resource,
            handle_evidence_resource,
            handle_export_resource,
        )

        self.resource_registry.register(SPEC_RESOURCE_TEMPLATE, handle_spec_resource)
        self.resource_registry.register(
            MEASUREMENT_RESOURCE_TEMPLATE, handle_measurement_resource
        )
        self.resource_registry.register(
            EVIDENCE_RESOURCE_TEMPLATE, handle_evidence_resource
        )
        self.resource_registry.register(
            EXPORT_RESOURCE_TEMPLATE, handle_export_resource
        )

    def _register_prompts(self) -> None:
        from specmetrics.mcp.prompts.templates import (
            MEASURE_PROJECT_PROMPT,
            ANALYZE_SPEC_PROMPT,
            EXPORT_RESULTS_PROMPT,
        )

        self.prompt_registry.register(MEASURE_PROJECT_PROMPT)
        self.prompt_registry.register(ANALYZE_SPEC_PROMPT)
        self.prompt_registry.register(EXPORT_RESULTS_PROMPT)

    def _track_request(self) -> None:
        self._active_requests += 1

    def _finish_request(self) -> None:
        self._active_requests = max(0, self._active_requests - 1)

    def _attach_handlers(self) -> None:
        if self._mcp_server is None:
            return

        mcp = self._mcp_server

        @mcp.list_tools()
        async def handle_list_tools() -> list:
            self._track_request()
            try:
                self.status.record_request()
                return self.tool_registry.list_tools()
            finally:
                self._finish_request()

        @mcp.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> list:
            self._track_request()
            try:
                self.status.record_request()
                params = arguments or {}
                self._validate_tool_params(name, params)
                handler = self.tool_registry.get_handler(name)
                if handler is None:
                    raise ToolError(-32601, f"Unknown tool: {name}")
                try:
                    return handler(params)
                except ToolError:
                    raise
                except Exception as exc:
                    self.status.record_error()
                    logger.error(
                        "tool_execution_failed", tool_name=name, error=str(exc)
                    )
                    raise ToolError(-32000, f"Tool execution failed: {exc}") from exc
            finally:
                self._finish_request()

        @mcp.list_resources()
        async def handle_list_resources() -> list:
            self._track_request()
            try:
                self.status.record_request()
                return self.resource_registry.list_templates()
            finally:
                self._finish_request()

        @mcp.read_resource()
        async def handle_read_resource(uri: str) -> str | bytes:
            self._track_request()
            try:
                self.status.record_request()
                handler = self.resource_registry.match_uri(uri)
                if handler is None:
                    raise ToolError(-32601, f"Resource not found: {uri}")
                try:
                    return handler(uri)
                except ToolError:
                    raise
                except Exception as exc:
                    self.status.record_error()
                    logger.error("resource_read_failed", uri=uri, error=str(exc))
                    raise ToolError(-32000, f"Failed to read resource: {exc}") from exc
            finally:
                self._finish_request()

        @mcp.list_prompts()
        async def handle_list_prompts() -> list:
            self._track_request()
            try:
                self.status.record_request()
                return self.prompt_registry.list_prompts()
            finally:
                self._finish_request()

        @mcp.get_prompt()
        async def handle_get_prompt(name: str, arguments: dict | None) -> dict:
            self._track_request()
            try:
                prompt = self.prompt_registry.get_prompt(name)
                if prompt is None:
                    raise ToolError(-32601, f"Unknown prompt: {name}")
                return prompt
            finally:
                self._finish_request()


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
