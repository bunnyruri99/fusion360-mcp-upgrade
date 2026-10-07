"""Typed wire protocol between MCP server and Fusion 360 add-in."""

from typing import Any

from pydantic import BaseModel

# Fusion 360 internal unit is centimeters.
# All public-facing API uses millimeters — convert at this layer.
MM_TO_CM = 0.1


class FusionRequest(BaseModel):
    tool: str
    args: dict[str, Any]
    timeout: float | None = None


class FusionResponse(BaseModel):
    success: bool
    message: str | None = None
    data: dict[str, Any] | None = None
    error: str | None = None


def mm_to_cm(value_mm: float) -> float:
    return value_mm * MM_TO_CM
