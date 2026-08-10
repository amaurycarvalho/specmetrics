"""MCP capability registration and request-handler wiring."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog
from mcp.types import TextContent

from specmetrics.mcp.registry import PromptRegistry, ResourceRegistry, ToolRegistry

from ._support import ToolError

if TYPE_CHECKING:
    from .server import MCPServer

logger = structlog.get_logger(__name__)


def refresh_capabilities(server: MCPServer) -> None:
    """Re-discover and register all tools, resources, and prompts.

    Called at startup to perform initial registration. May be called
    again at runtime to pick up newly installed plugins without a
    server restart (FR-012).  Currently registers statically defined
    capabilities; future versions may poll the Kernel capability
    registry for dynamic discovery.
    """
    server.tool_registry = ToolRegistry()
    server.resource_registry = ResourceRegistry()
    server.prompt_registry = PromptRegistry()
    register_tools(server)
    register_resources(server)
    register_prompts(server)
    logger.info(
        "mcp_capabilities_refreshed",
        tools=len(server.tool_registry.list_tools()),
        resources=len(server.resource_registry.list_templates()),
        prompts=len(server.prompt_registry.list_prompts()),
    )


def register_tools(server: MCPServer) -> None:
    """Register all MCP tools and their handlers."""
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

    registry = server.tool_registry
    registry.register(EXPLAIN_TOOL, handle_explain_measurement)
    registry.register(EXPLAIN_COMPARE_TOOL, handle_explain_compare)
    registry.register(RUN_PIPELINE_TOOL, handle_run_pipeline)
    registry.register(LIST_SPECS_TOOL, handle_list_specs)
    registry.register(READ_SPEC_TOOL, handle_read_spec)
    registry.register(EXPORT_RESULTS_TOOL, handle_export_results)
    registry.register(
        GET_STATUS_TOOL,
        lambda params: [
            TextContent(
                type="text",
                text=json.dumps(
                    {
                        "state": server.status.state.value,
                        "uptime_seconds": server.status.uptime,
                        "active_connections": server.status.active_connections,
                        "max_connections": server.status.max_connections,
                        "total_requests_handled": server.status.total_requests_handled,
                        "total_errors": server.status.total_errors,
                        "transport": server.status.transport.value,
                        "version": server.status.version,
                    },
                    indent=2,
                ),
            )
        ],
    )


def register_resources(server: MCPServer) -> None:
    """Register all MCP resource templates and their handlers."""
    from specmetrics.mcp.resources.measurements import (
        EVIDENCE_RESOURCE_TEMPLATE,
        EXPORT_RESOURCE_TEMPLATE,
        MEASUREMENT_RESOURCE_TEMPLATE,
        handle_evidence_resource,
        handle_export_resource,
        handle_measurement_resource,
    )
    from specmetrics.mcp.resources.specs import (
        SPEC_RESOURCE_TEMPLATE,
        handle_spec_resource,
    )

    registry = server.resource_registry
    registry.register(SPEC_RESOURCE_TEMPLATE, handle_spec_resource)
    registry.register(
        MEASUREMENT_RESOURCE_TEMPLATE, handle_measurement_resource
    )
    registry.register(
        EVIDENCE_RESOURCE_TEMPLATE, handle_evidence_resource
    )
    registry.register(
        EXPORT_RESOURCE_TEMPLATE, handle_export_resource
    )


def register_prompts(server: MCPServer) -> None:
    """Register all MCP prompts."""
    from specmetrics.mcp.prompts.templates import (
        ANALYZE_SPEC_PROMPT,
        EXPORT_RESULTS_PROMPT,
        MEASURE_PROJECT_PROMPT,
    )

    registry = server.prompt_registry
    registry.register(MEASURE_PROJECT_PROMPT)
    registry.register(ANALYZE_SPEC_PROMPT)
    registry.register(EXPORT_RESULTS_PROMPT)


def attach_handlers(server: MCPServer) -> None:
    """Attach the MCP server request handlers."""
    if server._mcp_server is None:
        return

    mcp = server._mcp_server

    @mcp.list_tools()
    async def handle_list_tools() -> list:
        server._track_request()
        try:
            server.status.record_request()
            return server.tool_registry.list_tools()
        finally:
            server._finish_request()

    @mcp.call_tool()
    async def handle_call_tool(name: str, arguments: dict | None) -> list:
        server._track_request()
        try:
            server.status.record_request()
            params = arguments or {}
            server._validate_tool_params(name, params)
            handler = server.tool_registry.get_handler(name)
            if handler is None:
                raise ToolError(-32601, f"Unknown tool: {name}")
            try:
                return handler(params)
            except ToolError:
                raise
            except Exception as exc:
                server.status.record_error()
                logger.error("tool_execution_failed", tool_name=name, error=str(exc))
                raise ToolError(-32000, f"Tool execution failed: {exc}") from exc
        finally:
            server._finish_request()

    @mcp.list_resources()
    async def handle_list_resources() -> list:
        server._track_request()
        try:
            server.status.record_request()
            return server.resource_registry.list_templates()
        finally:
            server._finish_request()

    @mcp.read_resource()
    async def handle_read_resource(uri: str) -> str | bytes:
        server._track_request()
        try:
            server.status.record_request()
            handler = server.resource_registry.match_uri(uri)
            if handler is None:
                raise ToolError(-32601, f"Resource not found: {uri}")
            try:
                return handler(uri)
            except ToolError:
                raise
            except Exception as exc:
                server.status.record_error()
                logger.error("resource_read_failed", uri=uri, error=str(exc))
                raise ToolError(-32000, f"Failed to read resource: {exc}") from exc
        finally:
            server._finish_request()

    @mcp.list_prompts()
    async def handle_list_prompts() -> list:
        server._track_request()
        try:
            server.status.record_request()
            return server.prompt_registry.list_prompts()
        finally:
            server._finish_request()

    @mcp.get_prompt()
    async def handle_get_prompt(name: str, arguments: dict | None) -> dict:
        server._track_request()
        try:
            prompt = server.prompt_registry.get_prompt(name)
            if prompt is None:
                raise ToolError(-32601, f"Unknown prompt: {name}")
            return prompt
        finally:
            server._finish_request()