"""Support types and state tracking for the MCP server."""

from __future__ import annotations

import time
import uuid
from enum import Enum
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from .server import ServerConfiguration


class ServerState(str, Enum):
    """Lifecycle state of the MCP server."""

    stopped = "stopped"
    starting = "starting"
    running = "running"
    stopping = "stopping"
    error = "error"


class TransportType(str, Enum):
    """Transport protocols supported by the MCP server."""

    stdio = "stdio"
    sse = "sse"


class LogLevel(str, Enum):
    """Logging verbosity levels."""

    debug = "debug"
    info = "info"
    warning = "warning"
    error = "error"


class MCPConnection:
    """Tracks a single MCP client connection."""

    def __init__(
        self: Self, transport_type: TransportType, protocol_version: str
    ) -> None:
        """Initialize the connection with transport and protocol metadata."""
        self.connection_id: str = uuid.uuid4().hex[:12]
        self.transport_type: TransportType = transport_type
        self.protocol_version: str = protocol_version
        self.connected_at: float = time.time()
        self.last_activity_at: float = time.time()
        self.active_request_id: str | None = None

    def touch(self: Self) -> None:
        """Record activity on the connection."""
        self.last_activity_at = time.time()


class ServerStatus:
    """Runtime status and metrics of the MCP server."""

    def __init__(self: Self, config: ServerConfiguration) -> None:
        """Initialize the status tracker from the server configuration."""
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

    def start(self: Self) -> None:
        """Mark the server as running."""
        self.state = ServerState.running
        self._start_time = time.time()

    def stop(self: Self) -> None:
        """Mark the server as stopped."""
        self.state = ServerState.stopped

    def record_request(self: Self) -> None:
        """Increment the total requests handled counter."""
        self.total_requests_handled += 1

    def record_error(self: Self) -> None:
        """Increment the error counter and record the error timestamp."""
        self.total_errors += 1
        self.last_error_timestamp = time.time()

    @property
    def uptime(self: Self) -> float:
        """Return the server uptime in seconds."""
        if self.state == ServerState.running:
            return time.time() - self._start_time
        return self.uptime_seconds


class ToolRequest:
    """Metadata for a single in-flight tool request."""

    def __init__(
        self: Self,
        request_id: str,
        tool_name: str,
        parameters: dict,
        connection_id: str,
    ) -> None:
        """Initialize the request with identifier and timing metadata."""
        self.request_id: str = request_id
        self.tool_name: str = tool_name
        self.parameters: dict = parameters
        self.received_at: float = time.time()
        self.connection_id: str = connection_id


class ToolError(Exception):
    """Error raised by tool or resource handlers."""

    def __init__(
        self: Self, code: int, message: str, details: dict | None = None
    ) -> None:
        """Initialize the error with a code, message, and optional details."""
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(code, message, details)


__all__ = [
    "LogLevel",
    "MCPConnection",
    "ServerState",
    "ServerStatus",
    "ToolError",
    "ToolRequest",
    "TransportType",
]