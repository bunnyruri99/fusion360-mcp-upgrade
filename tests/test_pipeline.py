"""Unit tests for batch export pipeline — no Fusion required."""

from unittest.mock import AsyncMock

from fusion360_mcp.fusion.errors import FusionConnectionError
from fusion360_mcp.fusion.protocol import FusionResponse
from fusion360_mcp.pipeline import VariantSpec, generate_variants

from .conftest import MockFusionClient


def make_variants(param_name: str, values: list[float], base_path: str) -> list[VariantSpec]:
    return [
        VariantSpec(
            parameters={param_name: v},
            export_path=f"{base_path}/{param_name}_{int(v)}.step",
        )
        for v in values
    ]


async def test_all_variants_succeed() -> None:
    client = MockFusionClient(FusionResponse(success=True, message="ok"))
    variants = make_variants("outer_diameter", [40.0, 50.0, 60.0], "C:/exports")
    report = await generate_variants(client, variants)

    assert report.total == 3
    assert report.succeeded == 3
    assert report.failed == 0
    assert report.success_rate == 1.0


async def test_parameter_set_before_export() -> None:
    client = MockFusionClient(FusionResponse(success=True, message="ok"))
    variants = [VariantSpec(parameters={"outer_diameter": 80.0}, export_path="C:/out/p.step")]
    await generate_variants(client, variants)

    tools_called = [c["tool"] for c in client.calls]
    assert "set_parameter" in tools_called
    set_idx = tools_called.index("set_parameter")
    export_idx = tools_called.index("export_step")
    assert set_idx < export_idx, "set_parameter must be called before export_step"


async def test_failed_variant_does_not_stop_pipeline() -> None:
    responses = [
        FusionResponse(success=False, error="Parameter not found: bad_param"),
        FusionResponse(success=True, message="ok"),
        FusionResponse(success=True, message="exported"),
    ]
    call_count = 0

    async def mock_send(request):
        nonlocal call_count
        if request.tool == "list_parameters":
            return FusionResponse(success=True, data={})
        resp = responses[min(call_count, len(responses) - 1)]
        call_count += 1
        return resp

    client = MockFusionClient()
    client.send = mock_send

    variants = [
        VariantSpec(parameters={"bad_param": 1.0}, export_path="C:/out/bad.step"),
        VariantSpec(parameters={"outer_diameter": 50.0}, export_path="C:/out/good.step"),
    ]
    report = await generate_variants(client, variants)

    assert report.total == 2
    assert report.failed == 1
    assert report.succeeded == 1


async def test_connection_error_captured_per_variant() -> None:
    client = MockFusionClient()
    client.send = AsyncMock(side_effect=FusionConnectionError("Add-in not running"))

    variants = make_variants("outer_diameter", [40.0], "C:/out")
    report = await generate_variants(client, variants)

    assert report.failed == 1
    assert "Add-in not running" in report.results[0].error


async def test_pipeline_report_summary_contains_filenames() -> None:
    client = MockFusionClient(FusionResponse(success=True, message="ok"))
    variants = make_variants("outer_diameter", [40.0, 50.0], "C:/out")
    report = await generate_variants(client, variants)

    summary = report.summary()
    assert "outer_diameter_40.step" in summary
    assert "outer_diameter_50.step" in summary
    assert "2/2" in summary


async def test_multiple_parameters_per_variant() -> None:
    client = MockFusionClient(FusionResponse(success=True, message="ok"))
    variants = [
        VariantSpec(
            parameters={"outer_diameter": 60.0, "wall_thickness": 5.0, "height": 30.0},
            export_path="C:/out/part.step",
        )
    ]
    await generate_variants(client, variants)
    set_calls = [c for c in client.calls if c["tool"] == "set_parameter"]
    assert len(set_calls) == 3
