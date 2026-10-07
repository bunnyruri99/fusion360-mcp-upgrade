# Parameter & Hole Tools

→ [Tool Kataloğu](../../tools/CATALOG.md) · [Export Tools](export-tools.md)

---

# Parametre Tools

Parametrik tasarımın motoru. `f360_create_parameter` ile yeni user parameter oluşturulur,
`f360_set_parameter` ile Fusion otomatik rebuild yapar — sonraki export güncel modeli verir.

Adlandırma kuralları: [knowledge/cad-naming-conventions.md](../../knowledge/cad-naming-conventions.md)

---

## f360_list_parameters

Aktif design'daki tüm user parameter'ları ve değerlerini listeler.

**Ön koşul:** Aktif design açık.  
**Sonuç:** Her parametre için `name: value unit` formatında liste.  
**Kullanım:** Hangi parametrelerin var olduğunu öğrenmek için — `f360_set_parameter`'dan önce çağır.

Argüman yok.

---

## f360_set_parameter

Mevcut user parameter değerini günceller. Güncelleme Fusion'ın otomatik rebuild'ini tetikler.

**Ön koşul:** Parametre Fusion'da zaten mevcut olmalı (`f360_list_parameters` ile doğrula).  
**Sonuç:** Parametre güncellenir, design rebuild edilir.  
**Kısıt:** Parametre adı Fusion'da göründüğü gibi tam eşleşmeli (büyük/küçük harf duyarlı).

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `name` | `string` | Fusion parametreler dialogundaki tam parametre adı |
| `value` | `number` | Yeni sayısal değer |
| `unit` | `string` | Birim kodu. Varsayılan: `"mm"`. Örnekler: `"mm"`, `"cm"`, `"deg"`, `"rad"` |

**Batch export için:**
```python
# pipeline.py ile:
variants = [
    VariantSpec({"outer_diameter": 40}, "exports/OD40.step"),
    VariantSpec({"outer_diameter": 50}, "exports/OD50.step"),
]
report = await generate_variants(client, variants)
```

---

## f360_create_parameter

Aktif design'a yeni user parameter ekler.

**Ön koşul:** Aynı isimde bir parameter olmamalı.
**Sonuç:** Parametre Fusion'ın user parameters listesine eklenir.
**Kısıt:** Birim kodu Fusion'ın tanıdığı birimlerden biri olmalı.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `name` | `string` | Oluşturulacak parametre adı |
| `value` | `number` | Başlangıç değeri |
| `unit` | `string` | Birim kodu. Varsayılan: `"mm"` |
| `comment` | `string` | Opsiyonel açıklama |

---

# Hole Tools

---

## f360_hole

En son oluşturulan solid body'nin üst yüzeyine delik açar.

**Ön koşul:** Solid body mevcut (`f360_extrude` veya `f360_revolve` çalıştırılmış).  
**Kısıt:** Pozisyon body sınırları içinde olmalı. `depth_mm` blind için zorunlu.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `diameter_mm` | `number ≥ 0.5` | Delik çapı, mm |
| `x_mm` | `number` | Üst yüzeyde merkez X konumu, mm (origin'den) |
| `y_mm` | `number` | Üst yüzeyde merkez Y konumu, mm (origin'den) |
| `hole_type` | `"through" \| "blind"` | Delik tipi. Varsayılan: `"through"` |
| `depth_mm` | `number ≥ 0.5` | Derinlik, mm — blind için zorunlu |

---

## f360_hole_pattern

Bolt circle üzerinde eşit aralıklı delik dizisi oluşturur.

**Ön koşul:** Solid body mevcut.  
**Kullanım:** Flanş cıvata delikleri, kapak montaj delikleri, PCD (Pitch Circle Diameter) kalıpları.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `hole_diameter_mm` | `number ≥ 0.5` | Her deliğin çapı, mm |
| `bolt_circle_dia_mm` | `number ≥ 1.0` | PCD — delik merkezlerinin oturduğu çemberin çapı, mm |
| `count` | `integer 2–36` | Eşit aralıklı delik sayısı |
| `hole_type` | `"through" \| "blind"` | Delik tipi. Varsayılan: `"through"` |
| `depth_mm` | `number ≥ 0.5` | Derinlik — blind için zorunlu |

**Örnek — 4 cıvatalı flanş:**
```
f360_hole_pattern(
    hole_diameter_mm=6.5,
    bolt_circle_dia_mm=70,
    count=4,
    hole_type="through"
)
```
