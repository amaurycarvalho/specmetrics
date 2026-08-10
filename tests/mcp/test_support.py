"""Tests for specmetrics.mcp._support types and state tracking."""

from __future__ import annotations

from specmetrics.mcp._support import (
    LogLevel,
    MCPConnection,
    ServerState,
    ServerStatus,
    ToolError,
    ToolRequest,
    TransportType,
)
from specmetrics.mcp.server import ServerConfiguration


class TestEnums:
    def test_server_state_members(self) -> None:
        assert ServerState.stopped.value == "stopped"
        assert ServerState.starting.value == "starting"
        assert ServerState.running.value == "running"
        assert ServerState.stopping.value == "stopping"
        assert ServerState.error.value == "error"

    def test_transport_type_members(self) -> None:
        assert TransportType.stdio.value == "stdio"
        assert TransportType.sse.value == "sse"

    def test_log_level_members(self) -> None:
        assert LogLevel.debug.value == "debug"
        assert LogLevel.info.value == "info"
        assert LogLevel.warning.value == "warning"
        assert LogLevel.error.value == "error"


class TestMCPConnection:
    def test_initial_values(self) -> None:
        conn = MCPConnection(TransportType.sse, "2025-03-26")
        assert conn.connection_id
        assert conn.transport_type == TransportType.sse
        assert conn.protocol_version == "2025-03-26"
        assert conn.last_activity_at >= conn.connected_at
        assert conn.active_request_id is None

    def test_touch_updates_last_activity(self) -> None:
        conn = MCPConnection(TransportType.stdio, "2025-03-26")
        original = conn.last_activity_at
        conn.touch()
        assert conn.last_activity_at >= original


class TestServerStatus:
    def test_initial_state(self) -> None:
        config = ServerConfiguration(transport=TransportType.sse, max_connections=5)
        status = ServerStatus(config)
        assert status.state == ServerState.stopped
        assert status.max_connections == 5
        assert status.transport == TransportType.sse
        assert status.total_requests_handled == 0
        assert status.total_errors == 0
        assert status.last_error_timestamp is None
        assert status.version == "2025-03-26"

    def test_start_and_stop(self) -> None:
        status = ServerStatus(ServerConfiguration())
        status.start()
        assert status.state == ServerState.running
        status.stop()
        assert status.state == ServerState.stopped

    def test_record_request(self) -> None:
        status = ServerStatus(ServerConfiguration())
        status.record_request()
        status.record_request()
        assert status.total_requests_handled == 2

    def test_record_error(self) -> None:
        status = ServerStatus(ServerConfiguration())
        status.record_error()
        assert status.total_errors == 1
        assert status.last_error_timestamp is not None

    def test_uptime_when_stopped_uses_saved_value(self) -> None:
        status = ServerStatus(ServerConfiguration())
        status.uptime_seconds = 12.5
        assert status.uptime == 12.5

    def test_uptime_when_running_is_positive(self) -> None:
        status = ServerStatus(ServerConfiguration())
        status.start()
        assert status.uptime >= 0


class TestToolRequest:
    def test_constructor_fields(self) -> None:
        request = ToolRequest(
            request_id="abc", tool_name="run_pipeline", parameters={"a": 1}, connection_id="conn1"
        )
        assert request.request_id == "abc"
        assert request.tool_name == "run_pipeline"
        assert request.parameters == {"a": 1}
        assert request.connection_id == "conn1"
        assert request.received_at > 0


class TestToolError:
    def test_constructor_with_details(self) -> None:
        err = ToolError(-32601, "not found", {"field": "x"})
        assert err.code == -32601
        assert err.message == "not found"
        assert err.details == {"field": "x"}

    def test_details_default_to_empty_dict(self) -> None:
        err = ToolError(-32000, "fail")
        assert err.details == {}
        assert str(err.args[0]) == "-32000"

class TestMCPConnectionMutationTargets:
    def test_connection_id_is_12_chars(self) -> None:
        conn = MCPConnection(TransportType.sse, "2025-03-26")
        assert len(conn.connection_id) == 12


class TestServerStatusMutationTargets:
    def test_uptime_seconds_defaults_to_zero(self) -> None:
        status = ServerStatus(ServerConfiguration())
        assert status.uptime_seconds == 0.0

    def test_start_time_defaults_to_zero(self) -> None:
        status = ServerStatus(ServerConfiguration())
        assert status._start_time == 0.0


class TestToolErrorArgs:
    def test_exception_args_include_all_three_values(self) -> None:
        err = ToolError(-32601, "not found", {"field": "x"})
        assert err.args == (-32601, "not found", {"field": "x"})

    def test_exception_args_with_default_details(self) -> None:
        err = ToolError(-32000, "fail")
        assert err.args == (-32000, "fail", None)
        assert err.details == {}
