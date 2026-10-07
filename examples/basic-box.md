# Örnek: Temel Dikdörtgen Kutu

**Senaryo:** "XY düzleminde 50×30×20mm dikdörtgen kutu oluştur"

**Kaç tool call:** 3

---

## Claude'a Söylenecek Prompt

```
Fusion'da XY düzleminde 50×30×20mm dikdörtgen kutu oluştur.
```

## Claude'un Ürettiği Tool Sequence

```
1. f360_create_sketch(plane="XY")
   → Çizim1 oluşturuldu

2. f360_draw_rectangle(width_mm=50, height_mm=30)
   → 50×30 mm dikdörtgen çizildi

3. f360_extrude(distance_mm=20)
   → 20mm extrude tamamlandı
```

## Opsiyonel Ekler

Fillet ile köşe yuvarlatma:
```
4. f360_fillet(radius_mm=2)
   → Fillet R2 mm uygulandı
```

STEP export:
```
5. f360_export_step(filepath="C:/exports/box_50x30x20_v1.step")
   → STEP exported
```
