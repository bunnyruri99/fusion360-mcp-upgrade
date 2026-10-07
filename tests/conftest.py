"""Shared test fixtures.

Key pattern: FusionClient is injectable → tests never need Fusion open.
MockFusionClient returns canned responses; test the MCP layer in isolation.
"""

from typing import Any
from unittest.mock import AsyncMock

import pytest

from fusion360_mcp.fusion.protocol import FusionResponse


class MockFusionClient:
    """Drop-in replacement for FusionClient in unit tests."""

    def __init__(self, response: FusionResponse | None = None) -> None:
        self.response = response or FusionResponse(success=True, message="ok")
        self.calls: list[dict[str, Any]] = []

    async def send(self, request) -> FusionResponse:
        self.calls.append({"tool": request.tool, "args": request.args})
        return self.response


@pytest.fixture
def mock_client() -> MockFusionClient:
    return MockFusionClient()


@pytest.fixture
def error_client() -> MockFusionClient:
    from fusion360_mcp.fusion.errors import FusionOperationError

    client = MockFusionClient()
    client.send = AsyncMock(side_effect=FusionOperationError("Fusion rejected the operation"))
    return client
