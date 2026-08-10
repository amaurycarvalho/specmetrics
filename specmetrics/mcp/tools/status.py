"""MCP tool definition for querying server status."""

from __future__ import annotations

from mcp.types import Tool

GET_STATUS_TOOL = Tool(
    name="get_status",
    description="Get the current status of the MCP server",
    inputSchema={
        "type": "object",
        "properties": {},
    },
)
