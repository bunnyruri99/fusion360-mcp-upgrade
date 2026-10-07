# Sketch Tools

→ [Tool Kataloğu](../../tools/CATALOG.md) · [Feature Tools](feature-tools.md)

Sketch tool'ları 2D profil oluşturur. Her 3D feature'dan önce çalıştırılır.

---

## f360_create_sketch

Aktif Fusion 360 design'ında bir construction plane üzerinde yeni sketch açar.

**Ön koşul:** Aktif design açık olmalı.  
**Sonuç:** Sketch oluşturulur, drawing tool'ları kullanılabilir hale gelir.  
**Kısıt:** Her `f360_draw_*` çağrısından önce çalıştırılmalı.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `plane` | `"XY" \| "XZ" \| "YZ"` | Sketch düzlemi |

**Düzlem rehberi:**
- `XY` — Top view, yassı parçalar için (en yaygın)
- `XZ` — Front view, profil extrude için
- `YZ` — Right-side view, yan profil için

```
Claude: f360_create_sketch(plane="XY")
Fusion: Çizim1 oluşturuldu
```

---

## f360_draw_rectangle

Aktif sketch'e (0, 0) noktasından başlayan iki noktalı dikdörtgen çizer.

**Ön koşul:** `f360_create_sketch` çalıştırılmış olmalı.  
**Kısıt:** Boyutlar milimetre cinsindendir, minimum 0.01mm.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `width_mm` | `number ≥ 0.01` | Genişlik (X yönü), mm |
| `height_mm` | `number ≥ 0.01` | Yükseklik (Y yönü), mm |

---

## f360_draw_circle

Aktif sketch'e (0, 0) merkezli daire çizer.

**Ön koşul:** `f360_create_sketch` çalıştırılmış olmalı.  
**Kullanım:** Silindirik parçalar, through-hole profili, boss geometrisi.  
**Kısıt:** Çap milimetre, minimum 0.01mm.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `diameter_mm` | `number ≥ 0.01` | Daire çapı, mm |

---

## Tipik Akış

```
f360_create_sketch(plane="XY")
    → f360_draw_rectangle(width_mm=60, height_mm=40)
    → f360_extrude(distance_mm=20)

f360_create_sketch(plane="XZ")
    → f360_draw_circle(diameter_mm=30)
    → f360_revolve(axis="X", angle_deg=360)
```
