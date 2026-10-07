# Sistem Mimarisi

> Bu belge, teknik bir müşterinin "bu sistem nasıl çalışıyor?" sorusunu 10 dakikada yanıtlar.

→ [README](../README.md) · [ADR Dizini](adr/) · [Bilinen Sorunlar](known-issues.md)

---

## Genel Bakış

```
Kullanıcı (doğal dil)
    │
    ▼
Claude Code / MCP Client
    │  stdio — JSON-RPC 2.0
    ▼
fusion360_mcp.server   (Python process, dışarıda çalışır)
    │  asyncio + run_in_executor
    ▼
fusion360_mcp.fusion.client   (TCP client, port 9876)
    │  TCP socket — JSON satır protokolü
    ▼
fusion360_mcp_bridge add-in   (Fusion 360 içinde çalışır)
    │  app.fireCustomEvent()
    ▼
_BridgeEventHandler.notify()   ← FUSION MAIN THREAD
    │  adsk.fusion / adsk.core / adsk.cam
    ▼
Fusion 360 Design
```

---

## Katman Sorumlulukları

### Katman 1: MCP Server (`src/fusion360_mcp/`)

**Ne yapar:** MCP protokolünü konuşur, tool şemalarını Claude'a sunar, tool çağrılarını TCP'ye iletir.

**Ne yapmaz:** Fusion API'sini hiç görmez. `adsk` import etmez.

```
server.py          ← tool routing, MCP protocol
tools/             ← tool tanımları + handler'lar (sadece FusionRequest gönderir)
fusion/client.py   ← async TCP bridge, injectable (testlerde mock'lanır)
fusion/protocol.py ← typed FusionRequest / FusionResponse
fusion/errors.py   ← 3 hata tipi: Connection, Timeout, Operation
```

### Katman 2: TCP Bridge

**Neden TCP?** Unix socket veya shared memory daha hızlı olurdu — ama platformlar arası taşınabilirlik ve Fusion'ın add-in sandbox'ı TCP'yi zorunlu kılar.

**Protokol:** Her mesaj `\n` ile sonlanan tek bir JSON satırı. İstek/yanıt çifti senkron — yanıt gelmeden yeni istek gönderilmez.

```json
İstek:  {"tool": "extrude", "args": {"distance_mm": 25}}\n
Yanıt:  {"success": true, "message": "Extruded 25 mm"}\n
```

### Katman 3: Fusion Add-in (`addin/`)

**Kritik kısıt:** Fusion 360 API'si (`adsk.*`) yalnızca UI main thread'den çağrılabilir. Worker thread'den çağrı → sessiz crash veya beklenmedik davranış.

**Çözüm: CustomEvent mimarisi**

```
TCP worker thread
    │
    ├─ JSON'u parse et
    ├─ UUID request ID oluştur
    ├─ threading.Event oluştur, _pending[id] = {event, result}
    └─ app.fireCustomEvent(CUSTOM_EVENT_ID, json.dumps({id, tool, args}))
                                │
                                └──► Fusion event queue'ya alır
                                         │
                               [Fusion main thread idle olduğunda]
                                         ▼
                               _BridgeEventHandler.notify()
                                    ├─ _dispatch(tool, args) çalışır
                                    ├─ adsk.fusion API güvenle çağrılır
                                    └─ _pending[id]["event"].set()
                                         │
                                [TCP worker thread uyanır]
                                         ▼
                               TCP response → MCP server → Claude
```

**GC Koruması:** `_BridgeEventHandler` nesnesi `_handlers` modül listesinde tutulur. Python GC handler'ı siler → Fusion sessizce crash eder.

---

## Veri Akışı — "50mm kare kutu çiz"

```
1. Kullanıcı: "XY düzleminde 50×30×20mm dikdörtgen kutu oluştur"

2. Claude LLM → tool sequence:
   f360_create_sketch(plane="XY")
   f360_draw_rectangle(width_mm=50, height_mm=30)
   f360_extrude(distance_mm=20)

3. Her tool call için:
   MCP server → FusionRequest → TCP → add-in → CustomEvent
   → main thread → adsk.fusion API → TCP response → MCP server → Claude

4. Toplam süre: ~3-6 saniye (3 sıralı TCP round-trip)
```

---

## Birim Dönüşümü

```
Kullanıcı/MCP Layer    →   mm   (okunabilir)
add-in _dispatch()     →   cm   (Fusion internal)

mm(value) = value * 0.1  ← TEK dönüşüm noktası (addin içinde)
```

Bu dönüşüm yalnızca `addin/fusion360_mcp_bridge.py` içindeki `mm()` fonksiyonunda yapılır. Başka bir yerde yapılırsa hata kaynağı ikiye katlanır.

---

## KVKK: Veri Nereye Gider?

| Senaryo | Veri Akışı | Dışarı Çıkıyor mu? |
|---------|-----------|-------------------|
| Varsayılan (FreeCAD backend, Faz 3) | Yerel process | **Hayır** |
| Forge backend (Faz 3) | Autodesk cloud | **Evet — consent zorunlu** |
| MCP server çalışırken | localhost TCP | **Hayır** |
| Claude Cloud | Yalnızca tool description + sonuç | Model vendor gizlilik politikası |

Forge backend aktifleştirmek için: `APS_FORGE_CONSENT=1` env değişkeni **ve** çağrı başına `forge_consent=True` parametresi gerekir. Double opt-in. ([ADR-0005](adr/0005-kvkk-forge-consent-gate.md))

---

## Bilinçli Tasarım Kararları

Her büyük kararın gerekçesi ADR dizininde:

| Karar | Neden | ADR |
|-------|-------|-----|
| CustomEvent yerine doğrudan API yok | Thread safety | [ADR-0001](adr/0001-customevent-over-direct-api.md) |
| FreeCAD önce, Forge sonra | KVKK + bağımlılık riski | [ADR-0002](adr/0002-freecad-as-default-backend.md) |
| F3D önce kaydet, sonra dönüştür | Atomik rollback | [ADR-0003](adr/0003-f3d-first-parallel-export.md) |
| Snapshot before variant | Parametre güvenliği | [ADR-0004](adr/0004-snapshot-before-variant.md) |
| Forge consent double opt-in | KVKK zorunluluğu | [ADR-0005](adr/0005-kvkk-forge-consent-gate.md) |
