"""Export tools — save Fusion designs to standard CAD/manufacturing formats."""

from mcp.types import TextContent, Tool

from ..fusion.client import FusionClient
from ..fusion.protocol import FusionRequest
from .registry import ToolEntry, ToolRegistry


def register(registry: ToolRegistry, client: FusionClient) -> None:
    registry.register(ToolEntry(
        definition=Tool(
            name="f360_export_step",
            description=(
                "Exports the active Fusion 360 design as a STEP file (.step). "
                "STEP is the universal interchange format for CAD — use for supplier quotes, "
                "CNC machining, or importing into other CAD tools. "
                "Provide an absolute file path including filename and .step extension."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute output path, e.g. C:/exports/bracket_v1.step"
                    }
                },
                "required": ["filepath"]
            }
        ),
        handler=lambda args: _export_step(client, args)
    ))

    registry.register(ToolEntry(
        definition=Tool(
            name="f360_export_stl",
            description=(
                "Exports the active Fusion 360 design as an STL file (.stl). "
                "STL is the standard format for 3D printing (FDM, SLA, SLS). "
                "mesh_refinement controls triangle density: "
                "'low' = fast/coarse (prototypes), 'medium' = default, 'high' = fine (visual/SLA)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Absolute output path, e.g. C:/exports/bracket_v1.stl"
                    },
                    "mesh_refinement": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "default": "medium",
                        "description": "Mesh density"
                    }
                },
                "required": ["filepath"]
            }
        ),
        handler=lambda args: _export_stl(client, args)
    ))


async def _export_step(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="export_step", args=args))
    return [TextContent(type="text", text=resp.message or f"Exported to {args['filepath']}")]


async def _export_stl(client: FusionClient, args: dict) -> list[TextContent]:
    resp = await client.send(FusionRequest(tool="export_stl", args=args))
    return [TextContent(type="text", text=resp.message or f"Exported to {args['filepath']}")]
