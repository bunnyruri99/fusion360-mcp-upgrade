"""Sketch tools — 2D drawing operations in Fusion 360.

IP note: tool description quality is the product. The LLM decides which
tool to call solely from this text. Vague descriptions = wrong calls.
"""

from mcp.types import TextContent, Tool

from ..fusion.client import FusionClient
from ..fusion.protocol import FusionRequest
from .registry import ToolEntry, ToolRegistry


def register(registry: ToolRegistry, client: FusionClient) -> None:
    registry.register(ToolEntry(
        definition=Tool(
            name="f360_create_sketch",
            description=(
                "Opens a new sketch on a construction plane in the active Fusion 360 design. "
                "MUST be called before any 2D drawing operation (draw_rectangle, draw_circle). "
                "XY = top view (most common for flat parts). "
                "XZ = front view. YZ = right-side view."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "plane": {
                        "type": "string",
                        "enum": ["XY", "XZ", "YZ"],
                        "description": "Construction plane for the sketch"
                    }
                },
                "required": ["plane"]
            }
        ),
        handler=lambda args: _create_sketch(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_draw_rectangle",
            description=(
                "Draws a 2-point rectangle originating from (0, 0) in the active sketch. "
                "f360_create_sketch must be called first. "
                "Dimensions are in millimeters. "
                "For a 50×30 mm rectangle: width_mm=50, height_mm=30."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "width_mm": {
                        "type": "number",
                        "minimum": 0.01,
                        "description": "Rectangle width in mm (X direction)"
                    },
                    "height_mm": {
                        "type": "number",
                        "minimum": 0.01,
                        "description": "Rectangle height in mm (Y direction)"
                    }
                },
                "required": ["width_mm", "height_mm"]
            }
        ),
        handler=lambda args: _draw_rectangle(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_draw_circle",
            description=(
                "Draws a circle centered at the origin (0, 0) in the active sketch. "
                "f360_create_sketch must be called first. "
                "Use for cylindrical shafts, bosses, through-holes, or circular pads. "
                "Diameter in millimeters."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "diameter_mm": {
                        "type": "number",
                        "minimum": 0.01,
                        "description": "Circle diameter in mm"
                    }
                },
                "required": ["diameter_mm"]
            }
        ),
        handler=lambda args: _draw_circle(client, args)
    ))


async def _create_sketch(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="create_sketch", args=args))
    return [TextContent(type="text", text=resp.message or "Sketch created")]


async def _draw_rectangle(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="draw_rectangle", args=args))
    return [TextContent(type="text", text=resp.message or "Rectangle drawn")]


async def _draw_circle(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="draw_circle", args=args))
    return [TextContent(type="text", text=resp.message or "Circle drawn")]
