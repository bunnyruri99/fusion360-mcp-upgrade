# Fusion API Patterns

> Fusion 360 API ile çalışırken öğrenilen kritik bilgiler.  
> Her madde bir tuzaktan veya keşiften kaynaklanıyor.

→ [INDEX](../INDEX.md) · [CAD Naming](cad-naming-conventions.md)

---

## Birim Dönüşümü

**Fusion 360 iç birimi santimetre.** Kullanıcıya her zaman mm göster.

```python
MM_TO_CM = 0.1

def mm(value: float) -> float:
    return value * MM_TO_CM
```

Bu dönüşüm **sadece add-in içinde** yapılır (`addin/fusion360_mcp_bridge.py`).  
MCP server ve tool dosyaları mm cinsinden konuşur.

---

## Thread Safety

Fusion 360 API **main thread dışından çağrılamaz.**

```
Worker thread (TCP server)
    ↓ app.fireCustomEvent()
Fusion main thread
    ↓ CustomEventHandler.notify()
    ↓ adsk.fusion API çağrıları — BURASI GÜVENLİ
    ↓ result → threading.Event.set()
Worker thread
    ↓ TCP response gönder
```

**Semptom:** Main thread dışından API çağrısı → sessiz çökme veya `RuntimeError`.

---

## Garbage Collection Koruması

```python
_handlers: list = []  # ZORUNLU — bu liste olmazsa handler GC tarafından silinir

handler = _BridgeEventHandler()
custom_event.add(handler)
_handlers.append(handler)  # burada tut
```

---

## Aktif Design Kontrolü

Her dispatch başında:

```python
design = adsk.fusion.Design.cast(app.activeProduct)
if design is None:
    return {"success": False, "error": "No active Fusion design."}
```

---

## Profile Seçimi

`extrude` için sketch'in kapalı bir profil içermesi şart:

```python
if sketch.profiles.count == 0:
    return {"success": False, "error": "No closed profile in sketch."}
profile = sketch.profiles.item(0)  # en son çizilen profil
```

Birden fazla profil varsa `item(0)` en büyüğü döndürür (Fusion davranışı).

---

## Export Manager

```python
export_mgr = design.exportManager

# STEP
options = export_mgr.createSTEPExportOptions(filepath)
export_mgr.execute(options)

# STL
options = export_mgr.createSTLExportOptions(root_component)
options.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementMedium
options.filename = filepath
export_mgr.execute(options)
```

---

## Parametre Güncelleme

```python
param = design.userParameters.itemByName(name)
if param is None:
    return {"success": False, "error": f"Parameter not found: {name}"}
param.expression = f"{value} {unit}"  # "50 mm", "2 deg" gibi
```

Parametre değiştiğinde Fusion otomatik rebuild yapar — sonraki export güncel modeli kullanır.

---

## Timeout Sınırı

Add-in → MCP server arası timeout: **30 saniye.**  
Karmaşık CAM operasyonları bu sınırı aşabilir — gelecekte ayarlanabilir hale getir.

---

## Bilinen Kısıtlar

| Kısıt | Durum |
|-------|-------|
| Tool'lar sıralı çalışır — batch gönderim add-in'i çökertir | ✅ Mimari gereği |
| Her tool call ayrı TCP bağlantısı | ✅ Tasarım gereği |
| Fusion UI donuyor — main thread meşgul olduğunda | ⚠️ Uzun işlemlerde beklenir |
| `runOnStartup: false` — her açılışta manuel başlatma | 🔜 Kullanıcı isteğine göre değiştirilebilir |
