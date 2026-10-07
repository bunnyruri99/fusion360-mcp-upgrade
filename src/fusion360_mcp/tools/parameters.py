"""Parameter tools — drive parametric design from outside Fusion."""

from mcp.types import TextContent, Tool

from ..fusion.client import FusionClient
from ..fusion.protocol import FusionRequest
from .registry import ToolEntry, ToolRegistry


def register(registry: ToolRegistry, client: FusionClient) -> None:
    registry.register(ToolEntry(
        definition=Tool(
            name="f360_create_parameter",
            description=(
                "Creates a named user parameter in the active Fusion 360 design. "
                "Use this before f360_set_parameter when a design does not already define "
                "the parameter. The value is numeric and unit defaults to mm."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Parameter name to create"
                    },
                    "value": {
                        "type": "number",
                        "description": "Initial numeric value"
                    },
                    "unit": {
                        "type": "string",
                        "default": "mm",
                        "enum": ["mm", "cm", "m", "in", "ft", "deg", "rad", "%"],
                        "description": (
                            "Unit string (mm, cm, deg, etc.) — must match Fusion's unit list"
                        )
                    },
                    "comment": {
                        "type": "string",
                        "description": "Optional comment shown in Fusion's parameter dialog"
                    }
                },
                "required": ["name", "value"]
            }
        ),
        handler=lambda args: _create_parameter(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_set_parameter",
            description=(
                "Updates a named user parameter in the active Fusion 360 design. "
                "The parameter must already exist (created manually in Fusion or via "
                "f360_create_parameter). "
                "Changing a parameter automatically rebuilds all features that reference it. "
                "Use this for batch variant generation: call once per variant, then export."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": (
                            "Exact parameter name as shown in the Fusion parameters dialog"
                        )
                    },
                    "value": {
                        "type": "number",
                        "description": "New numeric value"
                    },
                    "unit": {
                        "type": "string",
                        "default": "mm",
                        "enum": ["mm", "cm", "m", "in", "ft", "deg", "rad", "%"],
                        "description": (
                            "Unit string (mm, cm, deg, etc.) — must match Fusion's unit list"
                        )
                    }
                },
                "required": ["name", "value"]
            }
        ),
        handler=lambda args: _set_parameter(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_list_parameters",
            description=(
                "Returns all user parameters in the active Fusion 360 design "
                "with their current values and units. "
                "Call this first to see what parameters are available before calling "
                "f360_set_parameter."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        handler=lambda args: _list_parameters(client, args)
    ))


async def _create_parameter(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="create_parameter", args=args))
    return [TextContent(type="text", text=resp.message or "Parameter created")]


async def _set_parameter(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="set_parameter", args=args))
    return [TextContent(type="text", text=resp.message or "Parameter updated")]


async def _list_parameters(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="list_parameters", args=args))
    if resp.data:
        lines = [f"- {k}: {v}" for k, v in resp.data.items()]
        return [TextContent(type="text", text="\n".join(lines))]
    return [TextContent(type="text", text="No user parameters found")]
