# CAD Adlandırma Kuralları

> Bu kurallar fusion360-mcp'de oluşturulan tüm Fusion 360 modellerine uygulanır.  
> Tutarlı isimlendirme batch export ve parametre otomasyonunun çalışması için zorunludur.

→ [INDEX](../INDEX.md) · [Fusion API Patterns](fusion-api-patterns.md)

---

## 1. Parametre Adları

Parametre adları `f360_set_parameter` ile dışarıdan değiştirilir — bu yüzden tahmin edilebilir olması şart.

| Kural | Doğru | Yanlış |
|-------|-------|--------|
| `snake_case` | `outer_diameter` | `OuterDiameter`, `dis_cap` |
| Birim suffix | `wall_thickness_mm` (opsiyonel, netlik için) | `thickness` |
| Kısa ama açık | `bolt_circle_dia` | `bcd`, `d1` |
| İngilizce | `flange_height` | `flanş_yüksekliği` |

### Standart Parametre Sözlüğü

| Parametre | Anlamı |
|-----------|--------|
| `outer_diameter` | Dış çap |
| `inner_diameter` | İç çap |
| `wall_thickness` | Et kalınlığı |
| `flange_height` | Flanş yüksekliği |
| `bolt_circle_dia` | Cıvata daire çapı (BCD) |
| `bolt_hole_dia` | Cıvata delik çapı |
| `bolt_count` | Cıvata sayısı |
| `chamfer_size` | Pah boyutu |
| `fillet_radius` | Köşe yarıçapı |
| `thread_pitch` | Vida adımı |
| `length` | Genel uzunluk |
| `width` | Genel genişlik |
| `height` | Genel yükseklik |

---

## 2. Dosya Adları

### Fusion (.f3d) kayıt dosyaları

```
{part_name}_{revision}.f3d

flanş_v1.f3d
flanş_v2.f3d
bağlantı_parçası_v1.f3d
```

### Export dosyaları (STEP, STL)

```
{part_name}_{variant}_{revision}.step

flanş_OD80_v1.step
flanş_OD100_v1.step
bağlantı_M8_v2.step
```

| Alan | Değer | Örnek |
|------|-------|-------|
| `part_name` | snake_case, Türkçe kabul | `flanş`, `braket`, `kapak` |
| `variant` | değişen parametreyi yansıt | `OD80`, `M8`, `L150` |
| `revision` | `v1`, `v2` ... | `v1` |

---

## 3. Component (Assembly) Adları

```
PascalCase — açıklayıcı, tek kelime veya birleşik

Flanş
BoltPattern
MainBody
HousingCover
```

---

## 4. Sketch Adları

Fusion otomatik `Çizim1`, `Çizim2` atar — mümkünse rename et:

```
Profile_XY       ← ana profil, XY düzlemi
BoltHoles_Top    ← cıvata delikleri, üstten
Cutout_Front     ← kesit, önden
```

---

## 5. Feature / Timeline Adları

Fusion timeline'da her feature'ın adını değiştir:

```
Extrude_MainBody
Fillet_TopEdges
Shell_Housing
Mirror_BoltPattern
```

---

## 6. Batch Export Dosya Organizasyonu

```
exports/
├── {part_name}/
│   ├── {part_name}_{variant1}_{rev}.step
│   ├── {part_name}_{variant2}_{rev}.step
│   └── ...
└── index.csv    ← variant tablosu (opsiyonel)
```

Örnek:
```
exports/
└── flanş/
    ├── flanş_OD40_v1.step
    ├── flanş_OD50_v1.step
    ├── flanş_OD60_v1.step
    └── index.csv
```
