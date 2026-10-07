"""Batch export pipeline — parametrik varyant üretimi.

Kullanım:
    variants = [
        VariantSpec(parameters={"outer_diameter": 40}, export_path="C:/out/flange_OD40.step"),
        VariantSpec(parameters={"outer_diameter": 50}, export_path="C:/out/flange_OD50.step"),
    ]
    results = await generate_variants(client, variants)

Her varyant için:
  1. set_parameter çağrıları (Fusion otomatik rebuild yapar)
  2. STEP export
  3. Sonuç kaydedilir — hata tek varyantı durdurur, zinciri kesmez
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from .fusion.client import FusionClient
from .fusion.errors import FusionError
from .fusion.protocol import FusionRequest
from .snapshot import SnapshotGuard

logger = logging.getLogger(__name__)


@dataclass
class VariantSpec:
    """Tek bir varyantın tanımı."""
    parameters: dict[str, float]    # {"outer_diameter": 40.0, ...}
    export_path: str                 # "C:/exports/flange_OD40.step"
    unit: str = "mm"                 # tüm parametreler için varsayılan birim
    rollback_on_failure: bool = True # ADR-0004 snapshot rollback


@dataclass
class VariantResult:
    """Tek bir varyantın sonucu."""
    spec: VariantSpec
    success: bool
    message: str
    error: str | None = None
    params_set: list[str] = field(default_factory=list)


@dataclass
class PipelineReport:
    """Tüm batch işleminin özeti."""
    total: int
    succeeded: int
    failed: int
    results: list[VariantResult]

    @property
    def success_rate(self) -> float:
        return self.succeeded / self.total if self.total > 0 else 0.0

    def summary(self) -> str:
        lines = [
            f"Batch tamamlandı: {self.succeeded}/{self.total} başarılı",
        ]
        for r in self.results:
            status = "✓" if r.success else "✗"
            params = ", ".join(f"{k}={v}" for k, v in r.spec.parameters.items())
            lines.append(f"  {status} [{params}] → {Path(r.spec.export_path).name}")
            if r.error:
                lines.append(f"      Hata: {r.error}")
        return "\n".join(lines)


async def generate_variants(
    client: FusionClient,
    variants: list[VariantSpec],
    export_format: str = "step",
) -> PipelineReport:
    """Her varyant için parametreleri ayarla ve export et."""
    results: list[VariantResult] = []

    for i, spec in enumerate(variants, 1):
        logger.info("Varyant %d/%d: %s", i, len(variants), spec.parameters)
        result = await _process_variant(client, spec, export_format)
        results.append(result)
        if result.success:
            logger.info("  ✓ %s", result.message)
        else:
            logger.warning("  ✗ %s", result.error)

    succeeded = sum(1 for r in results if r.success)
    return PipelineReport(
        total=len(variants),
        succeeded=succeeded,
        failed=len(variants) - succeeded,
        results=results,
    )


async def _process_variant(
    client: FusionClient,
    spec: VariantSpec,
    export_format: str,
) -> VariantResult:
    params_set: list[str] = []

    try:
        async with SnapshotGuard(client, enabled=spec.rollback_on_failure) as guard:
            # 1. Parametreleri güncelle
            for name, value in spec.parameters.items():
                resp = await client.send(FusionRequest(
                    tool="set_parameter",
                    args={"name": name, "value": value, "unit": spec.unit},
                ))
                if not resp.success:
                    guard.mark_failed()
                    return VariantResult(
                        spec=spec,
                        success=False,
                        message="",
                        error=f"Parametre ayarlanamadı '{name}': {resp.error}",
                        params_set=params_set,
                    )
                params_set.append(name)

            # 2. Export
            export_tool = "export_step" if export_format == "step" else "export_stl"
            export_resp = await client.send(FusionRequest(
                tool=export_tool,
                args={"filepath": spec.export_path},
            ))
            if not export_resp.success:
                guard.mark_failed()
                return VariantResult(
                    spec=spec,
                    success=False,
                    message="",
                    error=f"Export başarısız: {export_resp.error}",
                    params_set=params_set,
                )

            return VariantResult(
                spec=spec,
                success=True,
                message=export_resp.message or f"Exported → {spec.export_path}",
                params_set=params_set,
            )

    except FusionError as exc:
        return VariantResult(
            spec=spec,
            success=False,
            message="",
            error=str(exc),
            params_set=params_set,
        )
