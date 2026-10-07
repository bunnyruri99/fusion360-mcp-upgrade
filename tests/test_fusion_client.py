"""Tests for the TCP client behavior."""

import asyncio
from collections.abc import Callable
from typing import Any

import pytest

from fusion360_mcp.fusion.client import FusionClient
from fusion360_mcp.fusion.protocol import FusionRequest, FusionResponse


class TrackingFusionClient(FusionClient):
    """Returns success without touching a real socket."""

    def __init__(self) -> None:
        super().__init__("127.0.0.1", 9876, 30.0)

    def _send_sync(self, request: FusionRequest) -> FusionResponse:
        return FusionResponse(success=True, message=request.tool)


class FakeLoop:
    """Async fake for run_in_executor that makes overlapping sends observable."""

    def __init__(self) -> None:
        self.active = 0
        self.max_active = 0

    def run_in_executor(
        self,
        executor: Any,
        func: Callable[[FusionRequest], FusionResponse],
        request: FusionRequest,
    ) -> asyncio.Task[FusionResponse]:
        return asyncio.create_task(self._run(func, request))

    async def _run(
        self,
        func: Callable[[FusionRequest], FusionResponse],
        request: FusionRequest,
    ) -> FusionResponse:
        self.active += 1
        self.max_active = max(self.max_active, self.active)
        try:
            await asyncio.sleep(0)
            return func(request)
        finally:
            self.active -= 1


async def test_client_serializes_tool_calls(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TrackingFusionClient()
    loop = FakeLoop()
    monkeypatch.setattr(asyncio, "get_event_loop", lambda: loop)
    monkeypatch.setattr(asyncio, "get_running_loop", lambda: loop)
    requests = [
        FusionRequest(tool="list_parameters", args={}),
        FusionRequest(tool="create_sketch", args={"plane": "XY"}),
        FusionRequest(tool="draw_rectangle", args={"width_mm": 50, "height_mm": 30}),
        FusionRequest(tool="extrude", args={"distance_mm": 20}),
    ]

    await asyncio.gather(*(client.send(req) for req in requests))

    assert loop.max_active == 1
