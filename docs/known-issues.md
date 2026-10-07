# Bilinen Sorunlar ve Workaround'lar

> Bu belge zamanla en değerli teknik belge haline gelir — sadece biz biliyoruz.

→ [INDEX](../INDEX.md) · [Fusion API Patterns](../knowledge/fusion-api-patterns.md)

---

## Fusion API Davranışları

### 1. Fusion iç birimi santimetre

**Sorun:** `adsk.fusion` tüm koordinat ve mesafeleri **cm** cinsinden bekler.  
`Point3D.create(5, 0, 0)` → 5cm = 50mm, kullanıcı 5mm bekliyor.

**Workaround:** Tüm mm→cm dönüşümü `mm()` helper ile tek yerden:
```python
def mm(v): return v * 0.1
```
Başka yerde dönüşüm yapmayın.

---

### 2. Tool'lar sıralı çalışmak zorunda

**Sorun:** Birden fazla tool çağrısının aynı anda gönderilmesi (batch) add-in'i çökertir veya tutarsız sonuç üretir.

**Neden:** Fusion ana thread'i sıralı işler. İki `fireCustomEvent` aynı anda tetiklenirse event queue bozulabilir.

**Workaround:** Her tool çağrısı önceki tamamlanmadan gönderilmez. `FusionClient.send()`
async lock ile tüm TCP çağrılarını serialize eder; `pipeline.py` de batch akışlarını sırayla işler.

---

### 3. Sketch profil sayısı beklenenden fazla

**Sorun:** Birden fazla kapalı profile sahip sketch'te `extrude` yanlış profili seçebilir.

**Neden:** `sketch.profiles.item(0)` en büyük profili döndürür (Fusion davranışı). İç içe geometrilerde beklenmedik sonuç üretir.

**Workaround (mevcut):** Her `create_sketch` → `draw_*` → `extrude` zincirinde tek profil kullanın. Multi-profil seçimi Faz 2'de.

---

### 4. Fillet tüm kenarları seçiyor

**Sorun:** `f360_fillet` solid body'nin **tüm** kenarlarına fillet uygular. Belirli kenar seçimi yok.

**Workaround:** Fillet'ı son adımda uygulayın. Seçici kenar fillet için Fusion'ı manuel kullanın.

**Planlanan:** `f360_fillet` Faz 2'de `edge_selection: "all" | "top" | "bottom"` desteği alacak.

---

### 5. Shell "en büyük yüzü" kaldırıyor

**Sorun:** `f360_shell` hangi yüzü kaldıracağını en büyük yüz alanı heuristiğiyle belirler. Karmaşık geometrilerde yanlış yüzü kaldırabilir.

**Workaround:** Shell'i basit dikdörtgen/silindirik gövdelere uygulayın. Özel yüz seçimi Faz 2'de.

---

### 6. GC Koruması — `_handlers` listesi

**Sorun:** Fusion, Python'ın `CustomEventHandler` nesnelerini kendi referans sayacıyla tutmaz. Python GC handler'ı siler → Fusion event geldiğinde NoneType crash.

**Workaround:** Handler oluşturulduktan sonra modül seviyesi `_handlers` listesine eklenmeli:
```python
handler = _BridgeEventHandler()
custom_event.add(handler)
_handlers.append(handler)  # bu satır olmazsa handler yaşamaz
```

---

### 7. Add-in yeniden başlatma gerektiriyor

**Sorun:** `fusion360_mcp_bridge.py` dosyası değiştirildikten sonra Fusion add-in'i reload etmez.

**Workaround:** Fusion → Tools → Add-Ins → `fusion360_mcp_bridge` → **Stop** → **Run**.

---

### 8. 30 saniye timeout

**Sorun:** TCP bridge `event.wait(timeout=30)` ile bekler. CAM toolpath hesaplaması gibi uzun işlemler zaman aşımına uğrar.

**Workaround:** Uzun işlemler için `.env`'de `FUSION_TIMEOUT=120` ayarlayın.  
`addin/fusion360_mcp_bridge.py` içindeki `TIMEOUT` sabitini de güncellemeniz gerekir.

---

### 9. macOS'ta add-in yolu farklı

**Sorun:** `%APPDATA%` Windows'a özgü. macOS'ta add-in dizini farklı.

**Doğru yollar:**
```
Windows: %APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\
macOS:   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/
```
