# Export Tools

→ [Tool Kataloğu](../../tools/CATALOG.md) · [Parameter Tools](parameter-tools.md)

---

## f360_export_step

Aktif Fusion 360 design'ını STEP dosyası olarak kaydeder.

**Ön koşul:** Solid body mevcut.  
**Kullanım:** Tedarikçi fiyat teklifi, CNC işleme, başka CAD yazılımlarına aktarım.  
**Format:** ISO 10303 AP214 (evrensel CAD değişim standardı).

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `filepath` | `string` | Tam dosya yolu, `.step` uzantılı. Örnek: `C:/exports/bracket_v1.step` |

**Adlandırma önerisi:** `{part_name}_{variant}_{revision}.step`  
Detay: [CAD Adlandırma Kuralları](../../knowledge/cad-naming-conventions.md)

---

## f360_export_stl

Aktif design'ı STL mesh dosyası olarak kaydeder.

**Ön koşul:** Solid body mevcut.  
**Kullanım:** FDM/SLA/SLS 3D baskı, görsel render, mesh analizi.  
**Kısıt:** STL parametrik bilgiyi korumaz — sadece geometri.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `filepath` | `string` | Tam dosya yolu, `.stl` uzantılı |
| `mesh_refinement` | `"low" \| "medium" \| "high"` | Üçgen yoğunluğu. Varsayılan: `"medium"` |

**Refinement rehberi:**
| Değer | Kullanım | Dosya boyutu |
|-------|---------|-------------|
| `"low"` | Hızlı prototip, FDM | Küçük |
| `"medium"` | Standart 3D baskı | Orta |
| `"high"` | SLA/DLP reçine, görsel | Büyük |

---

## Batch Export (pipeline.py)

Birden fazla varyantı tek çağrıyla export etmek için:

```python
from fusion360_mcp.pipeline import generate_variants, VariantSpec
from fusion360_mcp.fusion.client import FusionClient

client = FusionClient("127.0.0.1", 9876, timeout=30)

variants = [
    VariantSpec(
        parameters={"outer_diameter": d, "wall_thickness": 3},
        export_path=f"C:/exports/flange_OD{d}_v1.step"
    )
    for d in [40, 50, 60, 70, 80]
]

report = await generate_variants(client, variants)
print(report.summary())
# Batch tamamlandı: 5/5 başarılı
#   ✓ [outer_diameter=40] → flange_OD40_v1.step
#   ✓ [outer_diameter=50] → flange_OD50_v1.step
#   ...
```

Detay: [examples/batch-export.md](../../examples/batch-export.md)
