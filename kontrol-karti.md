# Fusion MCP — Hızlı Kontrol Kartı

> 30 saniyede nerede kaldığını bul.
> → [INDEX](INDEX.md) · [Rol Promptları](.claude/rol-promptlari.md) · [Tool Kataloğu](tools/CATALOG.md)

---

## Thread Safety — 5 Kural

```
1. adsk.*  → sadece _BridgeEventHandler.notify() içi (main thread)
2. Handler → _handlers.append(h) ZORUNLU (GC koruması)
3. fire    → event.wait(timeout=30) HER ZAMAN bekle
4. pending → timeout dalında da _pending.pop(req_id, None)
5. Birim   → kullanıcı mm, Fusion cm → /10.0 ile çevir
```

---

## Test Durumu — Modül × Test Eşlemesi

```
tools/sketch.py      → tests/test_tools/test_sketch.py       ✓  (3 test)
tools/features.py    → tests/test_tools/test_features.py      ✓  (5 test)
tools/holes.py       → tests/test_tools/test_features.py      ✓  (hole testleri dahil)
tools/parameters.py  → tests/test_tools/test_parameters.py   ✓  (5 test)
tools/export.py      → tests/test_tools/test_export.py        ✓  (4 test)
fusion/client.py     → —                                      ✗  EKSIK (mock yeterli şimdilik)

Faz 2:
pipeline.py          → tests/test_pipeline.py                 ✓  (6 test)
snapshot.py          → tests/test_snapshot.py                 —  BEKLIYOR
error_enricher.py    → tests/test_error_enricher.py           —  BEKLIYOR
```

---

## KVKK Kontrol Noktaları

```
forge_consent=False  → Forge HTTP çağrısı YOK
forge_consent=True   → APS_FORGE_CONSENT=1 env gerekli
Varsayılan backend   → yerel (veri dışarı çıkmaz)
```

---

## Faz Durumu

```
Faz 1 — Temel          [TAMAMLANDI]  ← 12 tool, 9 test, MCP bağlı
Faz 2 — Güvenilirlik   [DEVAM EDİYOR] ← pipeline.py ✓, snapshot, error_enricher
Faz 3 — Ölçeklendirme  [BEKLIYOR]
Faz 4 — Ürünleştirme   [BEKLIYOR]
```

---

## Bir Sonraki 3 Adım

```
1. error_enricher.py — LLM-readable hata mesajları (retryable, retry_with alanları)
2. snapshot.py — rollback mekanizması (generate_variants ile entegrasyon)
3. pipeline.py'e f360_tool olarak MCP server'a bağla → Claude'a "5 varyant üret" de
```

---

## Hızlı Test Komutu

```bash
python -m pytest tests/ -v --tb=short
```

## Add-in Durumu Kontrolü (PowerShell)

```powershell
$tcp = New-Object System.Net.Sockets.TcpClient
$tcp.Connect("127.0.0.1", 9876); "Add-in çalışıyor"; $tcp.Close()
```
