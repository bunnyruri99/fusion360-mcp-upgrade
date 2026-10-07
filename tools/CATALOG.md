# Tool Kataloğu

> Mevcut tüm f360_ tool'larının referansı.  
> Yeni tool eklediğinde bu dosyayı güncelle.

→ [INDEX](../INDEX.md) · [Tool Tasarım Prensipleri](../knowledge/tool-design-principles.md) · [f360-tool-designer skill](../.claude/skills/f360-tool-designer.md)

---

## Sketch

| Tool | Argümanlar | Açıklama |
|------|-----------|----------|
| `f360_create_sketch` | `plane: XY\|XZ\|YZ` | Yeni sketch açar — her çizimden önce |
| `f360_draw_rectangle` | `width_mm, height_mm` | Dikdörtgen (0,0)'dan |
| `f360_draw_circle` | `diameter_mm` | Daire (0,0) merkezli |

## 3D Features

| Tool | Argümanlar | Açıklama |
|------|-----------|----------|
| `f360_extrude` | `distance_mm` | Son profili solid body'e extrude et |
| `f360_fillet` | `radius_mm` | Son body'nin tüm kenarlarına fillet |
| `f360_shell` | `thickness_mm` | Son body'yi belirtilen et kalınlığıyla iç boşalt |

## Parametreler

| Tool | Argümanlar | Açıklama |
|------|-----------|----------|
| `f360_create_parameter` | `name, value, unit?, comment?` | Yeni user parameter oluştur |
| `f360_set_parameter` | `name, value, unit?` | User parameter güncelle → rebuild tetikler |
| `f360_list_parameters` | — | Tüm user parametrelerini listele |

## Export

| Tool | Argümanlar | Açıklama |
|------|-----------|----------|
| `f360_export_step` | `filepath` | STEP dosyası olarak kaydet |
| `f360_export_stl` | `filepath, mesh_refinement?` | STL dosyası olarak kaydet |

---

## Yol Haritası

| Öncelik | Tool | Alan | Notlar |
|---------|------|------|--------|
| ✅ | `f360_revolve` | Features | Silindirik parçalar — şaft, flanş |
| ✅ | `f360_hole`, `f360_hole_pattern` | Holes | Through/blind + bolt circle pattern |
| ✅ | `f360_create_parameter`, `f360_set_parameter`, `f360_list_parameters` | Parametreler | Parametre oluştur, güncelle, listele |
| 🔜 Orta | `f360_mirror` | Features | Pattern için |
| 🔜 Orta | `f360_thread` | Features | Vida dişi |
| 🔜 Orta | `f360_get_mass_properties` | Analiz | Ağırlık / atalet merkezi |
| 🔜 Düşük | `f360_cam_setup` | CAM | G-kod pipeline için temel |

---

## İstatistik

- **Toplam tool:** 13
- **Sketch:** 3
- **Features:** 4 (extrude, fillet, shell, revolve)
- **Holes:** 2 (hole, hole_pattern)
- **Parametreler:** 3
- **Export:** 2
