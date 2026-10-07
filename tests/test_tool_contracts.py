"""Contract tests for MCP tool metadata."""

import re

from fusion360_mcp.fusion.protocol import FusionResponse
from fusion360_mcp.server import build_registry

from .conftest import MockFusionClient


def test_tool_descriptions_reference_only_registered_tools() -> None:
    registry = build_registry(MockFusionClient(FusionResponse(success=True, message="ok")))
    tools = registry.list_tools()
    names = {tool.name for tool in tools}

    referenced_names = set()
    for tool in tools:
        referenced_names.update(re.findall(r"\bf360_[a-z0-9_]+\b", tool.description or ""))

    assert referenced_names <= names


def test_hole_tool_contract_matches_addin_capabilities() -> None:
    registry = build_registry(MockFusionClient(FusionResponse(success=True, message="ok")))
    hole_tool = next(tool for tool in registry.list_tools() if tool.name == "f360_hole")
    schema = getattr(hole_tool, "input_schema", None) or getattr(hole_tool, "inputSchema", None)
    properties = schema["properties"]

    assert properties["hole_type"]["enum"] == ["through", "blind"]
    assert "thread_size" not in properties
    assert "tapped" not in hole_tool.description.lower()
