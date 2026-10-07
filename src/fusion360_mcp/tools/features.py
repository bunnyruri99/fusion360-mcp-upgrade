"""3D feature tools — solid body operations in Fusion 360."""

from mcp.types import TextContent, Tool

from ..fusion.client import FusionClient
from ..fusion.protocol import FusionRequest
from .registry import ToolEntry, ToolRegistry


def register(registry: ToolRegistry, client: FusionClient) -> None:
    registry.register(ToolEntry(
        definition=Tool(
            name="f360_extrude",
            description=(
                "Extrudes the most recently created closed sketch profile into a 3D solid body. "
                "Call after f360_draw_rectangle or f360_draw_circle. "
                "Distance is in millimeters, positive = away from sketch plane. "
                "Creates a new body by default (not a cut)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "distance_mm": {
                        "type": "number",
                        "minimum": 0.01,
                        "description": "Extrusion depth in mm"
                    }
                },
                "required": ["distance_mm"]
            }
        ),
        handler=lambda args: _extrude(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_fillet",
            description=(
                "Applies a constant-radius fillet to all edges of the most recently "
                "created solid body. "
                "Use to remove sharp edges for DFM (manufacturing) or aesthetic purposes. "
                "Radius in millimeters. This tool currently fillets every edge on the latest body."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "radius_mm": {
                        "type": "number",
                        "minimum": 0.01,
                        "description": "Fillet radius in mm"
                    }
                },
                "required": ["radius_mm"]
            }
        ),
        handler=lambda args: _fillet(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_shell",
            description=(
                "Hollows out the most recently created solid body by removing one face and "
                "creating a uniform wall thickness. "
                "Use for enclosures, housings, or injection-molded parts. "
                "Thickness in millimeters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "thickness_mm": {
                        "type": "number",
                        "minimum": 0.1,
                        "description": "Wall thickness in mm"
                    }
                },
                "required": ["thickness_mm"]
            }
        ),
        handler=lambda args: _shell(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_revolve",
            description=(
                "Revolves the most recently created sketch profile around a construction axis "
                "to create a solid body of revolution (shaft, flange, boss, cup, etc.). "
                "Call after f360_draw_rectangle or any closed sketch profile. "
                "axis: X = lathe-style rotation around X-axis (most common for symmetric parts), "
                "Y = rotation around Y-axis. "
                "angle_deg: 360 = full solid of revolution, less = partial arc. "
                "Sketch profile must be on one side of the chosen axis."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "axis": {
                        "type": "string",
                        "enum": ["X", "Y"],
                        "description": (
                            "Construction axis to revolve around. "
                            "X = most common for symmetric parts."
                        )
                    },
                    "angle_deg": {
                        "type": "number",
                        "minimum": 1,
                        "maximum": 360,
                        "default": 360,
                        "description": "Sweep angle in degrees. 360 = full revolution."
                    }
                },
                "required": ["axis"]
            }
        ),
        handler=lambda args: _revolve(client, args)
    ))


async def _extrude(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="extrude", args=args))
    return [TextContent(type="text", text=resp.message or "Extrude complete")]


async def _fillet(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="fillet", args=args))
    return [TextContent(type="text", text=resp.message or "Fillet applied")]


async def _shell(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="shell", args=args))
    return [TextContent(type="text", text=resp.message or "Shell applied")]


async def _revolve(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="revolve", args=args))
    return [TextContent(type="text", text=resp.message or "Revolve complete")]
