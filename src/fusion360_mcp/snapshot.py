"""Parameter snapshot and restore guard for transactional pipeline executions.

Ref: ADR-0004 Snapshot-Before-Variant Rollback Stratejisi
"""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .fusion.client import FusionClient
from .fusion.errors import FusionError
from .fusion.protocol import FusionRequest

logger = logging.getLogger(__name__)


def parse_parameter_value(raw_val: Any) -> tuple[float, str]:
    """Parse raw value string or numeric into (value, unit).

    Examples:
        '40.0000 mm' -> (40.0, 'mm')
        '15.5' -> (15.5, 'mm')
        25 -> (25.0, 'mm')
    """
    if isinstance(raw_val, (int, float)):
        return float(raw_val), "mm"

    val_str = str(raw_val).strip()
    match = re.match(r"^([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)\s*([a-zA-Z%]*)$", val_str)
    if match:
        num = float(match.group(1))
        unit = match.group(2) or "mm"
        return num, unit

    # Fallback if unparseable unit string
    return float(val_str.split()[0]), "mm"


class SnapshotGuard:
    """Async context manager that snapshots parameters and rolls back on failure."""

    def __init__(self, client: FusionClient, enabled: bool = True) -> None:
        self.client = client
        self.enabled = enabled
        self.snapshot: dict[str, tuple[float, str]] = {}
        self._failed = False

    def mark_failed(self) -> None:
        """Mark current transaction as failed to trigger rollback on exit."""
        self._failed = True

    async def __aenter__(self) -> SnapshotGuard:
        if not self.enabled:
            return self

        try:
            resp = await self.client.send(FusionRequest(tool="list_parameters", args={}))
            if resp.success and resp.data:
                for k, v in resp.data.items():
                    try:
                        self.snapshot[k] = parse_parameter_value(v)
                    except Exception as ex:
                        logger.warning("Could not parse snapshot parameter %s=%r: %s", k, v, ex)
        except FusionError as exc:
            logger.warning("Failed to take parameters snapshot: %s", exc)

        return self

    async def restore(self) -> None:
        """Restore all parameters back to snapshot values."""
        if not self.enabled or not self.snapshot:
            return

        for name, (val, unit) in self.snapshot.items():
            try:
                await self.client.send(
                    FusionRequest(
                        tool="set_parameter",
                        args={"name": name, "value": val, "unit": unit},
                    )
                )
            except Exception as exc:
                logger.error("Failed to restore parameter '%s': %s", name, exc)

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if exc_val is not None or self._failed:
            await self.restore()
