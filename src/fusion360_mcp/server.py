"""MCP server entry point — wires everything together."""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from .config import settings
from .fusion.client import FusionClient
from .fusion.errors import FusionError
from .tools import export, features, holes, parameters, sketch, system
from .tools.registry import ToolRegistry

logging.basicConfig(level=logging.INFO, format="%(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


def build_registry(client: FusionClient) -> ToolRegistry:
    registry = ToolRegistry()
    system.register(registry, client)
    sketch.register(registry, client)
    features.register(registry, client)
    holes.register(registry, client)
    parameters.register(registry, client)
    export.register(registry, client)
    return registry


async def serve() -> None:
    client = FusionClient(
        host=settings.host,
        port=settings.port,
        timeout=settings.timeout,
    )
    registry = build_registry(client)
    server = Server("fusion360-mcp")

    @server.list_tools()
    async def list_tools():
        return registry.list_tools()

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = registry.get_handler(name)
        if handler is None:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        try:
            return await handler(arguments)
        except FusionError as exc:
            return [TextContent(type="text", text=f"Fusion error: {exc}")]

    logger.info(
        "fusion360-mcp starting — bridge at %s:%d", settings.host, settings.port
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    asyncio.run(serve())


if __name__ == "__main__":
    main()
