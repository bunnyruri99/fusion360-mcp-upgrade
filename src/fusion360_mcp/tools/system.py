"""System diagnostic and health-check tools."""

import json

from mcp.types import TextContent, Tool

from ..fusion.client import FusionClient
from ..fusion.protocol import FusionRequest
from .registry import ToolEntry, ToolRegistry


def register(registry: ToolRegistry, client: FusionClient) -> None:
    registry.register(ToolEntry(
        definition=Tool(
            name="f360_ping",
            description=(
                "Checks if the Fusion 360 add-in TCP bridge is running and responsive. "
                "Returns connectivity status, version, and whether an active design is open. "
                "Use this tool first to diagnose bridge readiness before issuing modeling commands."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        handler=lambda args: _ping(client, args)
    ))


async def _ping(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="ping", args=args))
    info = {
        "status": "connected" if resp.success else "error",
        "message": resp.message,
        "data": resp.data or {},
    }
    return [TextContent(type="text", text=json.dumps(info, indent=2))]
