from __future__ import annotations

from specmetrics.mcp.server import (
    MCPServer,
    ServerConfiguration,
    ServerState,
    TransportType,
)


class TestServerConfiguration:
    def test_default_config(self):
        config = ServerConfiguration()
        assert config.host == "127.0.0.1"
        assert config.port == 8100
        assert config.transport == TransportType.stdio
        assert config.max_connections == 10

    def test_from_yaml_missing_file(self):
        config = ServerConfiguration.from_yaml("/nonexistent/path.yml")
        assert config.host == "127.0.0.1"


class TestMCPServer:
    def test_initial_state(self):
        server = MCPServer()
        assert server.status.state == ServerState.stopped
        assert server.status.active_connections == 0

    def test_tool_registry_has_expected_tools(self):
        server = MCPServer()
        server._register_tools()
        tools = server.tool_registry.list_tools()
        names = [t.name for t in tools]
        assert "run_pipeline" in names
        assert "list_specs" in names
        assert "read_spec" in names
        assert "export_results" in names
        assert "get_status" in names

    def test_resource_registry_has_templates(self):
        server = MCPServer()
        server._register_resources()
        templates = server.resource_registry.list_templates()
        assert len(templates) > 0

    def test_prompt_registry_has_prompts(self):
        server = MCPServer()
        server._register_prompts()
        prompts = server.prompt_registry.list_prompts()
        assert len(prompts) > 0

    def test_protocol_version_check(self):
        server = MCPServer()
        assert server._check_protocol_version("2025-03-26") is True
        assert server._check_protocol_version("2099-01-01") is False

    def test_validate_tool_params_missing_required(self):
        server = MCPServer()
        server._register_tools()
        from specmetrics.mcp.server import ToolError
        import pytest
        with pytest.raises(ToolError):
            server._validate_tool_params("list_specs", {})

    def test_validate_tool_params_unknown(self):
        server = MCPServer()
        server._register_tools()
        from specmetrics.mcp.server import ToolError
        import pytest
        with pytest.raises(ToolError):
            server._validate_tool_params("nonexistent_tool", {})
