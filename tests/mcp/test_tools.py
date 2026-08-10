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


class TestResourceRegistry:
    def setup_method(self) -> None:
        from mcp.types import ResourceTemplate

        from specmetrics.mcp.registry import ResourceRegistry

        self.registry = ResourceRegistry()
        self.template = ResourceTemplate(
            uriTemplate="specmetrics://spec/{path}",
            name="Specification Document",
            description="Access specification document content by path",
            mimeType="text/markdown",
        )
        self.handler = lambda uri: f"content of {uri}"

    def test_register_stores_template_and_handler(self) -> None:
        self.registry.register(self.template, self.handler)
        templates = self.registry.list_templates()
        assert len(templates) == 1
        assert templates[0] == self.template

    def test_match_uri_returns_handler(self) -> None:
        self.registry.register(self.template, self.handler)
        handler = self.registry.match_uri("specmetrics://spec/foo.md")
        assert handler is self.handler

    def test_match_uri_returns_none_for_unmatched(self) -> None:
        self.registry.register(self.template, self.handler)
        assert self.registry.match_uri("specmetrics://other/x") is None

    def test_placeholder_regex_matches(self) -> None:
        self.registry.register(self.template, self.handler)
        assert self.registry.match_uri("specmetrics://spec/foo.md") is self.handler

    def test_two_templates_both_match(self) -> None:
        from mcp.types import ResourceTemplate

        t2 = ResourceTemplate(
            uriTemplate="specmetrics://measurement/{run_id}",
            name="Measurement",
        )
        handler2 = lambda uri: "measurement"
        self.registry.register(self.template, self.handler)
        self.registry.register(t2, handler2)
        assert self.registry.match_uri("specmetrics://spec/x.md") is self.handler
        assert self.registry.match_uri("specmetrics://measurement/run-1") is handler2


class TestPromptRegistry:
    def test_get_prompt_returns_registered(self) -> None:
        from mcp.types import Prompt

        from specmetrics.mcp.registry import PromptRegistry

        registry = PromptRegistry()
        prompt = Prompt(name="my_prompt", description="desc")
        registry.register(prompt)
        assert registry.get_prompt("my_prompt") is prompt

    def test_get_prompt_missing_returns_none(self) -> None:
        from specmetrics.mcp.registry import PromptRegistry

        registry = PromptRegistry()
        assert registry.get_prompt("missing") is None
