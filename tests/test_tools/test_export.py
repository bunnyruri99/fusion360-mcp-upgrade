"""Unit tests for export tools."""

import pytest

from fusion360_mcp.tools import export
from fusion360_mcp.tools.registry import ToolRegistry

from ..conftest import MockFusionClient


@pytest.fixture
def registry(mock_client: MockFusionClient) -> ToolRegistry:
    reg = ToolRegistry()
    export.register(reg, mock_client)
    return reg


async def test_all_export_tools_registered(registry: ToolRegistry) -> None:
    names = {t.name for t in registry.list_tools()}
    assert {"f360_export_step", "f360_export_stl"}.issubset(names)


async def test_export_step_sends_filepath(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_export_step")
    assert handler is not None
    await handler({"filepath": "C:/exports/flange_v1.step"})
    call = mock_client.calls[-1]
    assert call["tool"] == "export_step"
    assert call["args"]["filepath"] == "C:/exports/flange_v1.step"


async def test_export_stl_default_refinement(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_export_stl")
    assert handler is not None
    await handler({"filepath": "C:/exports/part.stl"})
    call = mock_client.calls[-1]
    assert call["tool"] == "export_stl"
    assert call["args"]["filepath"] == "C:/exports/part.stl"


async def test_export_stl_high_refinement(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_export_stl")
    assert handler is not None
    await handler({"filepath": "C:/exports/part_hq.stl", "mesh_refinement": "high"})
    call = mock_client.calls[-1]
    assert call["args"]["mesh_refinement"] == "high"
