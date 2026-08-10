"""Transport adapters for the MCP server."""

from __future__ import annotations

import abc
from typing import Self

from mcp.server import Server as MCPServerInstance
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server


class Transport(abc.ABC):
    """Abstract base for an MCP server transport."""

    def __init__(self: Self, mcp_server: MCPServerInstance) -> None:
        """Initialize the transport with the MCP server instance."""
        self._mcp_server = mcp_server

    @abc.abstractmethod
    async def run(self: Self) -> None:
        """Run the transport until interrupted."""
        ...


class StdioTransport(Transport):
    """MCP transport over standard input/output."""

    async def run(self: Self) -> None:
        """Run the MCP server over stdio."""
        async with stdio_server() as (read_stream, write_stream):
            await self._mcp_server.run(
                read_stream,
                write_stream,
                self._mcp_server.create_initialization_options(),
            )


class SSETransport(Transport):
    """MCP transport over Server-Sent Events (SSE)."""

    def __init__(
        self: Self,
        mcp_server: MCPServerInstance,
        host: str = "127.0.0.1",
        port: int = 8100,
    ) -> None:
        """Initialize the SSE transport with host and port bindings."""
        super().__init__(mcp_server)
        self.host = host
        self.port = port

    async def run(self: Self) -> None:
        """Run the MCP server over an SSE HTTP endpoint."""
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request) -> None:
            async with sse.connect_sse(
                request.scope,
                request.receive,
                request._send,
            ) as (read_stream, write_stream):
                await self._mcp_server.run(
                    read_stream,
                    write_stream,
                    self._mcp_server.create_initialization_options(),
                )

        async def handle_messages(request: Request) -> None:
            await sse.handle_post_message(request.scope, request.receive, request._send)

        app = Starlette(
            debug=False,
            routes=[
                Route("/sse", endpoint=handle_sse),
                Mount("/messages/", app=handle_messages),
            ],
        )

        import uvicorn

        await uvicorn.run(app, host=self.host, port=self.port, log_level="info")
