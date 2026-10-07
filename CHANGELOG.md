# Changelog

Keep a Changelog formatı — https://keepachangelog.com

## [Unreleased]

### Planlanan
- `error_enricher.py` — LLM-readable hata zenginleştirme (retryable/retry_with)
- `snapshot.py` — rollback mekanizması
- `f360_generate_variants` MCP tool — pipeline'ı Claude'dan çağır
- `f360_thread` / tapped delik desteği
- `tests/fusion_mocks.py` — merkezi adsk mock kütüphanesi

### Değişti
- MCP client tarafında Fusion tool çağrıları serialize edildi; eşzamanlı tool çağrıları artık TCP bridge'e paralel gönderilmez.
- Portable `.mcp.json` ve `run_server.bat`; kişisel Windows path'leri kaldırıldı.
- README ve katkı dokümantasyonundaki fork URL'i mevcut repo ile hizalandı.

### Eklendi
- `snapshot.py` — ADR-0004 snapshot-before-variant rollback mekanizması eklendi (`SnapshotGuard`).
- `tests/test_snapshot.py` — Snapshot parsing ve rollback birim testleri.
- `f360_ping` — MCP ve Add-in sağlık kontrolü (health check) tool'u eklendi (`tools/system.py`).
- `f360_create_parameter` tool'u ve add-in dispatch desteği.
- Tool metadata contract testleri.

### Düzeltildi
- `addin/fusion360_mcp_bridge.py`: Export dosyalarında path traversal ve hassas dizinlere yazma engellendi (`_validate_export_path`).
- `addin/fusion360_mcp_bridge.py`: `_handle_client` içindeki `assert app is not None` kaldırıldı, runtime check ve 64KB payload boyutu limiti eklendi.
- `addin/fusion360_mcp_bridge.py`: Parametre birimleri (`unit`) güvenli liste ile sınırlandırıldı.
- `client.py` & `protocol.py`: MCP sunucu ile Add-in arasında dinamik `timeout` senkronizasyonu sağlandı.
- `client.py`: `asyncio.get_event_loop()` deprecated çağrısı `asyncio.get_running_loop()` ile değiştirildi.
- `config.py`: `Settings` sınıfı `@dataclass(frozen=True)` yapılarak güvenli hale getirildi, `dotenv` opsiyonel fallback eklendi.
- `addin/fusion360_mcp_bridge.py`: 230 satırlık `_dispatch` if-chain yapısı modüler `_TOOL_HANDLERS` dictionary tablosuna dönüştürüldü.
- `run_server.bat`: Betiğin doğru dizinden çalışması ve hata durumunda hata kodunu bildirmesi sağlandı.
- `f360_hole` artık tapped/thread desteği varmış gibi davranmıyor; desteklenen tipler `through` và `blind`.
- Tool açıklamalarında bulunmayan `f360_chamfer` referansı kaldırıldı.

---

## [0.1.0] — 2026-06-06

### Eklendi
- MCP server (`src/fusion360_mcp/server.py`) — resmi `mcp` kütüphanesi, stdio transport
- Fusion 360 add-in TCP bridge (`addin/fusion360_mcp_bridge/`) — CustomEvent + worker thread mimarisi
- **Sketch tools**: `f360_create_sketch`, `f360_draw_rectangle`, `f360_draw_circle`
- **Feature tools**: `f360_extrude`, `f360_fillet`, `f360_shell`, `f360_revolve`
- **Hole tools**: `f360_hole` (through/blind/tapped), `f360_hole_pattern` (bolt circle)
- **Parameter tools**: `f360_set_parameter`, `f360_list_parameters`
- **Export tools**: `f360_export_step`, `f360_export_stl`
- `pipeline.py` — batch export orkestrasyonu, `generate_variants()`, `PipelineReport`
- `ToolRegistry` — modüler tool kayıt sistemi, injectable `FusionClient`
- `MockFusionClient` — Fusion olmadan birim testi
- 24 test (pytest, asyncio)
- Claude Code MCP entegrasyonu — project scope kayıt
- Vault dokümantasyonu: `INDEX.md`, `knowledge/`, `tools/CATALOG.md`, `kontrol-karti.md`
- Rol bazlı workflow: `rol-promptlari.md` (Architect/Builder/Tester/Reviewer/Debugger)

### Teknik Kararlar
- Fusion iç birimi CM — mm→cm dönüşümü yalnızca add-in'de `mm()` helper ile
- `_handlers` modül listesi — GC koruması zorunlu
- Async executor — TCP I/O event loop'u bloklamaz
- `f360_` prefix — tool namespace, multi-server ortamda çakışma önler

---

<!-- bağlantılar -->
[Unreleased]: https://github.com/iamtechnoana/fusion360-mcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/iamtechnoana/fusion360-mcp/releases/tag/v0.1.0
