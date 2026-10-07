"""Unit tests for features and hole tools."""

import pytest

from fusion360_mcp.tools import features, holes
from fusion360_mcp.tools.registry import ToolRegistry

from ..conftest import MockFusionClient


@pytest.fixture
def registry(mock_client: MockFusionClient) -> ToolRegistry:
    reg = ToolRegistry()
    features.register(reg, mock_client)
    holes.register(reg, mock_client)
    return reg


async def test_all_feature_tools_registered(registry: ToolRegistry) -> None:
    names = {t.name for t in registry.list_tools()}
    assert {"f360_extrude", "f360_fillet", "f360_shell", "f360_revolve"}.issubset(names)


async def test_all_hole_tools_registered(registry: ToolRegistry) -> None:
    names = {t.name for t in registry.list_tools()}
    assert {"f360_hole", "f360_hole_pattern"}.issubset(names)


async def test_revolve_default_angle(registry: ToolRegistry, mock_client: MockFusionClient) -> None:
    handler = registry.get_handler("f360_revolve")
    assert handler is not None
    await handler({"axis": "X"})
    call = mock_client.calls[-1]
    assert call["tool"] == "revolve"
    assert call["args"]["axis"] == "X"


async def test_hole_through_sends_correct_args(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_hole")
    assert handler is not None
    await handler({"diameter_mm": 8.0, "x_mm": 20.0, "y_mm": 15.0, "hole_type": "through"})
    call = mock_client.calls[-1]
    assert call["tool"] == "hole"
    assert call["args"]["diameter_mm"] == 8.0
    assert call["args"]["hole_type"] == "through"


async def test_hole_pattern_count(registry: ToolRegistry, mock_client: MockFusionClient) -> None:
    handler = registry.get_handler("f360_hole_pattern")
    assert handler is not None
    await handler({"hole_diameter_mm": 6.0, "bolt_circle_dia_mm": 60.0, "count": 4})
    call = mock_client.calls[-1]
    assert call["args"]["count"] == 4
    assert call["args"]["bolt_circle_dia_mm"] == 60.0
