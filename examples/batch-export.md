# Örnek: Batch Export — Parametrik Varyant Üretimi

**Senaryo:** Flanşın 5 farklı dış çap versiyonunu tek seferde STEP olarak üret.

**Ön koşul:** Fusion'da `outer_diameter` user parameter'ı tanımlanmış, aktif flanş modeli açık.

---

## Claude'a Söylenecek Prompt

```
Açık Fusion modelinde outer_diameter parametresini 40, 50, 60, 70, 80 değerleri için
güncelle ve her varyantı C:/exports/flange/ klasörüne STEP olarak export et.
```

## Claude'un Ürettiği Tool Sequence

```
1. f360_list_parameters()
   → outer_diameter: 40.0000 mm, wall_thickness: 3.0000 mm

2. f360_set_parameter(name="outer_diameter", value=40)
   f360_export_step(filepath="C:/exports/flange/flange_OD40_v1.step")

3. f360_set_parameter(name="outer_diameter", value=50)
   f360_export_step(filepath="C:/exports/flange/flange_OD50_v1.step")

4. f360_set_parameter(name="outer_diameter", value=60)
   f360_export_step(filepath="C:/exports/flange/flange_OD60_v1.step")

5. f360_set_parameter(name="outer_diameter", value=70)
   f360_export_step(filepath="C:/exports/flange/flange_OD70_v1.step")

6. f360_set_parameter(name="outer_diameter", value=80)
   f360_export_step(filepath="C:/exports/flange/flange_OD80_v1.step")
```

**Toplam süre:** ~60-90 saniye (10 TCP round-trip)

## Python Kodu ile (pipeline.py)

```python
import asyncio
from fusion360_mcp.pipeline import generate_variants, VariantSpec
from fusion360_mcp.fusion.client import FusionClient

async def main():
    client = FusionClient("127.0.0.1", 9876, timeout=30)
    variants = [
        VariantSpec(
            parameters={"outer_diameter": d},
            export_path=f"C:/exports/flange/flange_OD{d}_v1.step"
        )
        for d in [40, 50, 60, 70, 80]
    ]
    report = await generate_variants(client, variants)
    print(report.summary())

asyncio.run(main())
```

## Beklenen Çıktı

```
Batch tamamlandı: 5/5 başarılı
  ✓ [outer_diameter=40] → flange_OD40_v1.step
  ✓ [outer_diameter=50] → flange_OD50_v1.step
  ✓ [outer_diameter=60] → flange_OD60_v1.step
  ✓ [outer_diameter=70] → flange_OD70_v1.step
  ✓ [outer_diameter=80] → flange_OD80_v1.step
```

## Müşteriye Söylenecek Şey

> "Geçen saat süren 5 farklı ebat STEP üretimini 90 saniyeye indirdik. 
>  Sayı 50'ye çıksa da süre lineer ölçeklenir."
