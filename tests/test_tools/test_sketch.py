"""Unit tests for sketch tools — no Fusion 360 required."""

import pytest

from fusion360_mcp.tools import sketch
from fusion360_mcp.tools.registry import ToolRegistry

from ..conftest import MockFusionClient


@pytest.fixture
def registry(mock_client: MockFusionClient) -> ToolRegistry:
    reg = ToolRegistry()
    sketch.register(reg, mock_client)
    return reg


async def test_create_sketch_xy(registry: ToolRegistry, mock_client: MockFusionClient) -> None:
    handler = registry.get_handler("f360_create_sketch")
    assert handler is not None
    result = await handler({"plane": "XY"})
    assert result[0].text == "ok"
    assert mock_client.calls[-1] == {"tool": "create_sketch", "args": {"plane": "XY"}}


async def test_draw_rectangle_sends_mm(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_draw_rectangle")
    assert handler is not None
    await handler({"width_mm": 50.0, "height_mm": 30.0})
    call = mock_client.calls[-1]
    assert call["args"]["width_mm"] == 50.0
    assert call["args"]["height_mm"] == 30.0


async def test_unknown_tool_returns_none(registry: ToolRegistry) -> None:
    assert registry.get_handler("f360_does_not_exist") is None


async def test_all_sketch_tools_registered(registry: ToolRegistry) -> None:
    names = {t.name for t in registry.list_tools()}
    assert {"f360_create_sketch", "f360_draw_rectangle", "f360_draw_circle"}.issubset(names)
