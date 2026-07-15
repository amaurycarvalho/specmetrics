from __future__ import annotations

import abc

from mcp.server import Server as MCPServerInstance
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server


class Transport(abc.ABC):
    def __init__(self, mcp_server: MCPServerInstance):
        self._mcp_server = mcp_server

    @abc.abstractmethod
    async def run(self) -> None:
        ...


class StdioTransport(Transport):
    async def run(self) -> None:
        async with stdio_server() as (read_stream, write_stream):
            await self._mcp_server.run(
                read_stream,
                write_stream,
                self._mcp_server.create_initialization_options(),
            )


class SSETransport(Transport):
    def __init__(self, mcp_server: MCPServerInstance, host: str = "127.0.0.1", port: int = 8100):
        super().__init__(mcp_server)
        self.host = host
        self.port = port

    async def run(self) -> None:
        from starlette.applications import Starlette
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request):
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

        async def handle_messages(request):
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
