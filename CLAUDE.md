# Fusion MCP — Bertalanffy Labs

## Proje
Autodesk Fusion 360'ı MCP (Model Context Protocol) üzerinden AI agent'larla
kontrol eden pipeline sistemi. Endüstriyel SME'lere parametrik CAD otomasyonu
ve batch export sunar.

**Geliştirici:** Gözde Eraslan — Bertalanffy Labs. Mekanik mühendislik + AI sistemleri.

---

## Dosya Mimarisi (tek sorumluluk kuralı)

```
fusion360-mcp/
├── CLAUDE.md                        ← bu dosya
├── INDEX.md                         ← vault haritası
├── .mcp.json                        ← Claude Code bağlantı config
│
├── src/fusion360_mcp/
│   ├── server.py                    ← stdio MCP server (dış process)
│   ├── config.py                    ← .env ile ayarlar
│   ├── fusion/
│   │   ├── client.py                ← TCP bridge (async, injectable)
│   │   ├── protocol.py              ← typed request/response + mm→cm
│   │   └── errors.py                ← 3 hata tipi
│   └── tools/
│       ├── registry.py              ← tool kayıt sistemi
│       ├── sketch.py                ← f360_create_sketch, draw_rect, draw_circle
│       ├── features.py              ← f360_extrude, fillet, shell, revolve
│       ├── holes.py                 ← f360_hole, hole_pattern
│       ├── parameters.py            ← f360_set_parameter, list_parameters
│       └── export.py                ← f360_export_step, export_stl
│
├── addin/fusion360_mcp_bridge/      ← Fusion add-in (Fusion içi)
│   ├── fusion360_mcp_bridge.py
│   └── fusion360_mcp_bridge.manifest
│
├── knowledge/                       ← bilgi tabanı
│   ├── cad-naming-conventions.md
│   ├── fusion-api-patterns.md
│   └── tool-design-principles.md
│
├── tools/CATALOG.md                 ← tool envanteri
│
├── tests/
│   ├── conftest.py                  ← MockFusionClient (Fusion gerektirmez)
│   ├── test_tools/test_sketch.py
│   └── test_tools/test_features.py
│
│ — Faz 2+ modüller (henüz yazılmadı, aşağıda planlandı) —
│
├── pipeline.py                      ← batch export orkestrasyonu
├── snapshot.py                      ← rollback mekanizması
├── retry.py                         ← hata sınıflandırma
├── error_enricher.py                ← LLM-readable hata zenginleştirme
├── converter.py                     ← FreeCAD + Forge backend'leri
├── fallback.py                      ← backend fallback zinciri
├── parallel_export.py               ← worker pool koordinatörü
├── cache_manager.py                 ← F3D cache yaşam döngüsü
├── healing.py                       ← self-healing motoru
└── snapshot_store.py                ← kalıcı snapshot depolama
```

---

## Kritik Teknik Kurallar

### Fusion API (ihlali crash'e yol açar)
- **Tüm `adsk.*` çağrıları main thread'den yapılır** — worker thread'den asla
- **`_handlers` listesi modül seviyesinde tutulur** — GC koruması zorunlu
- **Fusion iç birimi CM** — kullanıcı mm, tüm değerler `/10` ile çevrilir
- `fireCustomEvent` → kuyruk, anlık değil; `event.wait()` her zaman gerekli
- `markerPosition` sadece Parametric Design modunda çalışır

### Modül Sınırları
```
fusion/client.py  → adsk bağımsız, sadece TCP
tools/            → adsk bağımsız, sadece FusionRequest gönderir
addin/            → tüm adsk.* çağrıları burada
pipeline.py       → snapshot.py + converter.py kullanır (Faz 2)
error_enricher.py → adsk bağımsız, saf Python (Faz 2)
converter.py      → subprocess + urllib, adsk bağımsız (Faz 2)
```

### Thread Safety
- Worker thread'den Fusion API'ye **asla** doğrudan erişim yok
- `_pending` dict: her timeout'dan sonra `pop(req_id, None)` ile temizlenir
- TCP server `daemon=True` thread'de çalışır

### KVKK
- Forge backend **yalnızca** `forge_consent=True` ile aktif
- `APS_FORGE_CONSENT=1` env değişkeni olmadan Forge HTTP çağrısı yapılmaz
- Varsayılan backend: yerel (veri dışarı çıkmaz)

---

## Test Kuralları

```bash
# Fusion gerektirmeyen testler (her zaman çalışır)
python -m pytest tests/ -v

# Fusion add-in açıkken TCP testi
python -c "import socket; s=socket.create_connection(('127.0.0.1',9876)); s.close(); print('OK')"
```

- Mock'lar `tests/conftest.py`'de toplanır: `MockFusionClient`
- Fusion olmadan birim testi zorunlu
- Her yeni tool → test_tools/ altında test

---

## Tool Description Standartı (MCP)

Her tool description şu üç bilgiyi içerir:
1. **Ön koşul**: "ÖNCE X çağrılmış olmalı"
2. **Çıktı**: başarı mesajı ne döndürür
3. **Kısıt**: birim (mm), sınır değer, özel durum

---

## Hata Yönetimi Standardı

Her `_dispatch()` bloğu:
1. `success=True` veya `success=False` döndürür — exception fırlatmaz
2. `error` alanı LLM'e okunabilir mesaj içerir
3. (Faz 2) `retryable` ve `retry_with` alanları LLM'e rehberlik eder

---

## Aktif Geliştirme Odağı

**Faz 1 — Temel [TAMAMLANDI]**
- [x] MCP server (stdio, resmi `mcp` kütüphanesi)
- [x] Fusion add-in TCP bridge (CustomEvent, thread safety)
- [x] Tool kütüphanesi: sketch, extrude, fillet, shell, revolve, hole, hole_pattern, parametreler, export
- [x] MockFusionClient tabanlı birim testler (9 test, Fusion gerektirmez)
- [x] Claude Code MCP entegrasyonu (`fusion360` server, project scope)
- [x] Vault yapısı: INDEX.md, knowledge/, tools/CATALOG.md
- [x] CAD adlandırma kuralları, Fusion API patterns, tool tasarım prensipleri
- [x] Rol bazlı workflow sistemi (rol-promptlari.md, kontrol-karti.md)

**Faz 2 — Güvenilirlik [BEKLIYOR]**
- [ ] `error_enricher.py` — LLM-readable hata zenginleştirme
- [ ] `snapshot.py` + SnapshotGuard — rollback
- [ ] `pipeline.py` — batch export orkestrasyonu
- [ ] `tests/fusion_mocks.py` — merkezi adsk mock kütüphanesi
- [ ] Entegrasyon testleri

**Faz 3 — Ölçeklendirme [BEKLIYOR]**
- [ ] `parallel_export.py` worker pool
- [ ] `cache_manager.py` TTL politikaları
- [ ] `healing.py` self-healing döngüsü

**Faz 4 — Ürünleştirme [BEKLIYOR]**
- [ ] Docker paketleme
- [ ] `snapshot_store.py` PLM entegrasyonu
- [ ] Müşteri onboarding dokümantasyonu

---

## Komutlar

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v
python -m fusion360_mcp.server
```

Add-in: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\fusion360_mcp_bridge`
