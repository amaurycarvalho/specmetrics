from __future__ import annotations

from specmetrics.mcp.server import MCPServer


class TestMCPServerTools:
    def setup_method(self) -> None:
        self.server = MCPServer()
        self.server._register_tools()

    def test_measure_tool_schema(self):
        tool_def = self.server.tool_registry.get_tool("run_pipeline")
        assert tool_def is not None
        assert "project_path" in tool_def.inputSchema.get("required", [])

    def test_list_specs_tool_schema(self):
        tool_def = self.server.tool_registry.get_tool("list_specs")
        assert tool_def is not None

    def test_read_spec_tool_schema(self):
        tool_def = self.server.tool_registry.get_tool("read_spec")
        assert tool_def is not None
        assert "spec_path" in tool_def.inputSchema.get("required", [])

    def test_export_results_tool_schema(self):
        tool_def = self.server.tool_registry.get_tool("export_results")
        assert tool_def is not None
        assert "format" in tool_def.inputSchema.get("required", [])

    def test_get_status_tool_schema(self):
        tool_def = self.server.tool_registry.get_tool("get_status")
        assert tool_def is not None
