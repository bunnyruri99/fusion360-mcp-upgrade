"""Hole tools — ISO-aligned hole operations in Fusion 360.

Holes are a separate module because they are fundamentally different from
sketch-based features: they operate on existing solid faces, not profiles.
"""

from mcp.types import TextContent, Tool

from ..fusion.client import FusionClient
from ..fusion.protocol import FusionRequest
from .registry import ToolEntry, ToolRegistry


def register(registry: ToolRegistry, client: FusionClient) -> None:
    registry.register(ToolEntry(
        definition=Tool(
            name="f360_hole",
            description=(
                "Creates a hole on the top face of the most recently created solid body. "
                "Requires an existing solid body (call f360_extrude or f360_revolve first). "
                "Position is measured from the body origin in mm. "
                "hole_type: "
                "'through' = passes all the way through the body; "
                "'blind' = stops at depth_mm from the top face. "
                "Use for mounting holes and clearance holes. Threaded holes are not yet supported."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "diameter_mm": {
                        "type": "number",
                        "minimum": 0.5,
                        "description": "Hole diameter in mm"
                    },
                    "x_mm": {
                        "type": "number",
                        "description": (
                            "X position of hole center on the top face, in mm from origin"
                        )
                    },
                    "y_mm": {
                        "type": "number",
                        "description": (
                            "Y position of hole center on the top face, in mm from origin"
                        )
                    },
                    "hole_type": {
                        "type": "string",
                        "enum": ["through", "blind"],
                        "default": "through",
                        "description": "Hole type: through or blind"
                    },
                    "depth_mm": {
                        "type": "number",
                        "minimum": 0.5,
                        "description": (
                            "Hole depth in mm — required for 'blind', ignored for 'through'"
                        )
                    }
                },
                "required": ["diameter_mm", "x_mm", "y_mm"]
            }
        ),
        handler=lambda args: _hole(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_hole_pattern",
            description=(
                "Creates multiple equally-spaced holes in a circular bolt-circle pattern "
                "on the top face of the most recently created solid body. "
                "Used for flanges, covers, and bolt-pattern connections. "
                "bolt_circle_dia_mm is the diameter of the circle on which hole centers sit. "
                "All holes are the same diameter and type."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "hole_diameter_mm": {
                        "type": "number",
                        "minimum": 0.5,
                        "description": "Diameter of each hole in mm"
                    },
                    "bolt_circle_dia_mm": {
                        "type": "number",
                        "minimum": 1.0,
                        "description": (
                            "Bolt circle diameter (PCD) in mm — circle on which all "
                            "hole centers lie"
                        )
                    },
                    "count": {
                        "type": "integer",
                        "minimum": 2,
                        "maximum": 36,
                        "description": "Number of holes equally spaced around the bolt circle"
                    },
                    "hole_type": {
                        "type": "string",
                        "enum": ["through", "blind"],
                        "default": "through",
                        "description": "Hole type for all holes in the pattern"
                    },
                    "depth_mm": {
                        "type": "number",
                        "minimum": 0.5,
                        "description": "Depth in mm — required for 'blind' type"
                    }
                },
                "required": ["hole_diameter_mm", "bolt_circle_dia_mm", "count"]
            }
        ),
        handler=lambda args: _hole_pattern(client, args)
    ))


async def _hole(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="hole", args=args))
    return [TextContent(type="text", text=resp.message or "Hole created")]


async def _hole_pattern(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="hole_pattern", args=args))
    return [TextContent(type="text", text=resp.message or "Hole pattern created")]
