# Feature Tools

→ [Tool Kataloğu](../../tools/CATALOG.md) · [Sketch Tools](sketch-tools.md) · [Hole Tools](parameter-tools.md)

3D solid body operasyonları. Her zaman mevcut bir sketch profilinden başlar.

---

## f360_extrude

En son oluşturulan kapalı sketch profilini 3D solid body'e extrude eder.

**Ön koşul:** `f360_draw_rectangle` veya `f360_draw_circle` çalıştırılmış, kapalı profil mevcut.  
**Sonuç:** Yeni solid body oluşturulur (cut değil).  
**Kısıt:** Sketch'te kapalı profil yoksa hata döner.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `distance_mm` | `number ≥ 0.01` | Extrusion derinliği, mm. Pozitif = sketch düzleminden uzağa. |

---

## f360_revolve

En son oluşturulan kapalı sketch profilini bir eksen etrafında döndürerek solid body oluşturur.

**Ön koşul:** Sketch profili oluşturulmuş, profil seçilen eksenin **bir tarafında** olmalı.  
**Kullanım:** Şaft, flanş, boss, iç/dış silindir, kapak.  
**Kısıt:** Profil ekseni keserse hata üretir.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `axis` | `"X" \| "Y"` | Döndürme ekseni. X = tornalama tipi (en yaygın). |
| `angle_deg` | `number 1–360` | Açı, derece. 360 = tam döner cisim. Varsayılan: 360. |

**Örnek — şaft:**
```
f360_create_sketch(plane="XZ")
f360_draw_rectangle(width_mm=10, height_mm=50)  # profil eksenden uzakta
f360_revolve(axis="X", angle_deg=360)           # silindir oluşur
```

---

## f360_fillet

En son oluşturulan solid body'nin tüm kenarlarına sabit yarıçaplı fillet uygular.

**Ön koşul:** Solid body mevcut (`f360_extrude` veya `f360_revolve` çalıştırılmış).  
**Kullanım:** DFM (üretilebilirlik), estetik, keskin kenar kaldırma.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `radius_mm` | `number ≥ 0.01` | Fillet yarıçapı, mm. |

**Not:** Tüm kenarlar seçilir. Seçici kenar fillet Faz 2'de planlandı.

---

## f360_shell

En son oluşturulan solid body'yi iç boşaltır; en büyük yüz kaldırılır, uniform et kalınlığı oluşturulur.

**Ön koşul:** Solid body mevcut.  
**Kullanım:** Enclosure, housing, enjeksiyon kalıp parçaları.  
**Kısıt:** Et kalınlığı body boyutlarıyla fiziksel olarak uyumlu olmalı. Minimum 0.1mm.

| Argüman | Tip | Açıklama |
|---------|-----|----------|
| `thickness_mm` | `number ≥ 0.1` | Et kalınlığı, mm. |
