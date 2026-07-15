from __future__ import annotations

import logging

import structlog
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .tools import (
    EXPORT_TOOL,
    PLUGINS_LIST_TOOL,
    VERSION_TOOL,
    TOOL_HANDLERS,
    MEASURE_TOOL,
)

structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger(__name__)

server = Server("specmetrics")


@server.list_tools()
async def handle_list_tools() -> list:
    return [MEASURE_TOOL, PLUGINS_LIST_TOOL, VERSION_TOOL, EXPORT_TOOL]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list:
    if name not in TOOL_HANDLERS:
        logger.error("unknown_tool", tool_name=name)
        raise ValueError(f"Unknown tool: {name}")

    logger.info("tool_called", tool_name=name, arguments=arguments)
    handler = TOOL_HANDLERS[name]
    return handler(arguments or {})


async def main() -> None:
    logger.info("mcp_server_starting")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


if __name__ == "__main__":
    import anyio

    anyio.run(main)
