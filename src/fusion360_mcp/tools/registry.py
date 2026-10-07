"""Tool registry — decouples tool definitions from the MCP server wiring."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import Any

from mcp.types import TextContent, Tool

ToolHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, list[TextContent]]]


@dataclass
class ToolEntry:
    definition: Tool
    handler: ToolHandler


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolEntry] = {}

    def register(self, entry: ToolEntry) -> None:
        self._tools[entry.definition.name] = entry

    def list_tools(self) -> list[Tool]:
        return [e.definition for e in self._tools.values()]

    def get_handler(self, name: str) -> ToolHandler | None:
        entry = self._tools.get(name)
        return entry.handler if entry else None
