# Tool Tasarım Prensipleri

> Fusion 360 MCP tool'larının description kalitesi = IP kalitesi.  
> LLM sadece bu metni okuyarak hangi tool'u ne zaman çağıracağına karar verir.

→ [INDEX](../INDEX.md) · [f360-tool-designer skill](../.claude/skills/f360-tool-designer.md)

---

## Temel Kural

```
Zayıf description → LLM yanlış tool seçer veya yanlış argüman üretir
Güçlü description → güvenilir otomasyon
```

---

## Description Anatomisi

Her tool description 4 soruyu yanıtlamalı:

```
1. NE YAPAR    — tek cümle, fiille başla
2. NE ZAMAN    — önceki hangi tool çalışmış olmalı
3. BİRİM       — mm, deg, vb. açıkça yaz
4. SINIR/ÖZEL  — ne yapamaz, ne olur hatalı girdide
```

### Kötü örnek:
```python
description="Extrudes a profile."
```

### İyi örnek:
```python
description=(
    "Extrudes the most recently created closed sketch profile into a 3D solid body. "  # NE
    "Call after f360_draw_rectangle or f360_draw_circle. "                              # NE ZAMAN
    "Distance is in millimeters, positive = away from sketch plane. "                   # BİRİM
    "Creates a new body by default (not a cut)."                                        # SINIR
)
```

---

## Argüman Şeması

`description` alanı LLM'e gösteriliyor — birim ve sınırları buraya yaz:

```python
"distance_mm": {
    "type": "number",
    "minimum": 0.01,
    "description": "Extrusion depth in mm"   # ← birim burada
}
```

---

## Namespace Kuralı

Tüm tool'lar `f360_` prefix'i ile başlar.  
Multi-server ortamda çakışmayı önler.

```
f360_create_sketch   ✅
create_sketch        ❌ (hangi CAD yazılımı?)
```

---

## Sıralı Çalışma Zinciri

Tool description'lar zinciri açıkça belirtmeli:

```
f360_create_sketch
    ↓ "MUST be called before any 2D drawing operation"
f360_draw_rectangle / f360_draw_circle
    ↓ "Requires f360_create_sketch to be called first"
f360_extrude
    ↓ "Call after f360_draw_rectangle or f360_draw_circle"
f360_fillet / f360_shell / f360_export_step
```

---

## Yeni Tool Checklist

- [ ] `f360_` prefix var mı?
- [ ] Description 4 soruyu yanıtlıyor mu?
- [ ] Her argümanda birim yazıyor mu?
- [ ] Add-in `_dispatch()` fonksiyonuna eklendi mi?
- [ ] Test var mı (MockFusionClient ile)?
- [ ] [CATALOG.md](../tools/CATALOG.md) güncellendi mi?
