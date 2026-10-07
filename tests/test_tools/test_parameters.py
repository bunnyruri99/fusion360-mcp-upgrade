"""Unit tests for parameter tools."""

import pytest

from fusion360_mcp.fusion.protocol import FusionResponse
from fusion360_mcp.tools import parameters
from fusion360_mcp.tools.registry import ToolRegistry

from ..conftest import MockFusionClient


@pytest.fixture
def registry(mock_client: MockFusionClient) -> ToolRegistry:
    reg = ToolRegistry()
    parameters.register(reg, mock_client)
    return reg


async def test_all_parameter_tools_registered(registry: ToolRegistry) -> None:
    names = {t.name for t in registry.list_tools()}
    assert {"f360_set_parameter", "f360_list_parameters"}.issubset(names)


async def test_set_parameter_sends_correct_args(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_set_parameter")
    assert handler is not None
    await handler({"name": "outer_diameter", "value": 80.0, "unit": "mm"})
    call = mock_client.calls[-1]
    assert call["tool"] == "set_parameter"
    assert call["args"]["name"] == "outer_diameter"
    assert call["args"]["value"] == 80.0
    assert call["args"]["unit"] == "mm"


async def test_create_parameter_sends_correct_args(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_create_parameter")
    assert handler is not None
    await handler({"name": "wall_thickness", "value": 3.0, "unit": "mm"})
    call = mock_client.calls[-1]
    assert call["tool"] == "create_parameter"
    assert call["args"]["name"] == "wall_thickness"
    assert call["args"]["value"] == 3.0
    assert call["args"]["unit"] == "mm"


async def test_set_parameter_default_unit(
    registry: ToolRegistry, mock_client: MockFusionClient
) -> None:
    handler = registry.get_handler("f360_set_parameter")
    assert handler is not None
    await handler({"name": "wall_thickness", "value": 3.0})
    call = mock_client.calls[-1]
    assert call["args"]["name"] == "wall_thickness"


async def test_list_parameters_empty(registry: ToolRegistry) -> None:
    handler = registry.get_handler("f360_list_parameters")
    assert handler is not None
    result = await handler({})
    assert len(result) == 1
    assert "ok" in result[0].text.lower() or "parameter" in result[0].text.lower()


async def test_list_parameters_with_data() -> None:
    client = MockFusionClient(
        FusionResponse(
            success=True,
            message="2 parameters found",
            data={"outer_diameter": "80.0000 mm", "wall_thickness": "3.0000 mm"},
        )
    )
    reg = ToolRegistry()
    parameters.register(reg, client)
    handler = reg.get_handler("f360_list_parameters")
    result = await handler({})
    text = result[0].text
    assert "outer_diameter" in text
    assert "wall_thickness" in text
