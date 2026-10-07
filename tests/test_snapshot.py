"""Unit tests for parameter snapshot and rollback guard (ADR-0004)."""

import pytest
from fusion360_mcp.fusion.protocol import FusionResponse
from fusion360_mcp.pipeline import VariantSpec, generate_variants
from fusion360_mcp.snapshot import SnapshotGuard, parse_parameter_value

from .conftest import MockFusionClient


def test_parse_parameter_value() -> None:
    val, unit = parse_parameter_value("40.0000 mm")
    assert val == 40.0
    assert unit == "mm"

    val, unit = parse_parameter_value("25.5 cm")
    assert val == 25.5
    assert unit == "cm"

    val, unit = parse_parameter_value(50)
    assert val == 50.0
    assert unit == "mm"


async def test_snapshot_guard_restores_on_failure() -> None:
    calls = []

    async def mock_send(req):
        calls.append(req)
        if req.tool == "list_parameters":
            return FusionResponse(
                success=True,
                data={"outer_diameter": "40.0000 mm", "height": "20.0000 mm"},
            )
        if req.tool == "set_parameter":
            return FusionResponse(success=True, message="updated")
        if req.tool == "export_step":
            return FusionResponse(success=False, error="Export failed")
        return FusionResponse(success=True)

    client = MockFusionClient()
    client.send = mock_send

    spec = VariantSpec(
        parameters={"outer_diameter": 60.0},
        export_path="C:/out/f.step",
        rollback_on_failure=True,
    )

    report = await generate_variants(client, [spec])
    assert report.failed == 1

    # Check that set_parameter was called to restore original values (40.0)
    restore_calls = [
        c for c in calls
        if c.tool == "set_parameter" and c.args.get("name") == "outer_diameter" and c.args.get("value") == 40.0
    ]
    assert len(restore_calls) >= 1
