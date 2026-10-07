# fusion360-mcp — Proje Vault

> Fusion 360 API'yi MCP protokolü üzerinden kontrol eden Python paketi.  
> Bertalanffy Labs · Makine Mühendisliği IP Serisi · v0.1

---

## Başlangıç Noktası

| Soru | Bak |
|------|-----|
| Bu ne, neden var? | [CLAUDE.md](CLAUDE.md) |
| Hangi tool'lar var? | [tools/CATALOG.md](tools/CATALOG.md) |
| Şu an nerede kaldım? | [kontrol-karti.md](kontrol-karti.md) |
| Claude Code'u nasıl kullanırım? | [.claude/rol-promptlari.md](.claude/rol-promptlari.md) |
| Yeni tool nasıl eklenir? | [.claude/skills/f360-tool-designer.md](.claude/skills/f360-tool-designer.md) |
| CAD dosyaları nasıl adlandırılır? | [knowledge/cad-naming-conventions.md](knowledge/cad-naming-conventions.md) |
| Fusion API tuzakları neler? | [knowledge/fusion-api-patterns.md](knowledge/fusion-api-patterns.md) |
| Batch export nasıl çalışır? | [examples/batch_export.py](examples/batch_export.py) |

---

## Mimari Harita

```
Claude Code / MCP client
    │ stdio JSON-RPC
    ▼
src/fusion360_mcp/server.py          ← [Kaynak](src/fusion360_mcp/server.py)
    │
    ├── tools/sketch.py              ← [Sketch araçları](src/fusion360_mcp/tools/sketch.py)
    ├── tools/features.py            ← [3D feature araçları](src/fusion360_mcp/tools/features.py)
    ├── tools/parameters.py          ← [Parametre araçları](src/fusion360_mcp/tools/parameters.py)
    └── tools/export.py              ← [Export araçları](src/fusion360_mcp/tools/export.py)
    │
    └── fusion/client.py             ← TCP bridge → port 9876
    │
addin/fusion360_mcp_bridge/          ← Fusion add-in (ayrı kurulum)
    └── [Kurulum notu](addin/README.md)
```

---

## Dokümantasyon

| Belge | İçerik |
|-------|--------|
| [docs/architecture.md](docs/architecture.md) | Sistem mimarisi, katmanlar, veri akışı, KVKK |
| [docs/design-philosophy.md](docs/design-philosophy.md) | Bertalanffy Labs felsefesi — GST, Prigogine, Autopoiesis |
| [docs/known-issues.md](docs/known-issues.md) | Fusion API tuzakları, workaround'lar |
| [docs/adr/](docs/adr/) | 5 ADR — mimari kararların gerekçeleri |
| [docs/tools/](docs/tools/) | Tool referans sayfaları (sketch, feature, parameter, export) |
| [examples/](examples/) | Yapıştırılabilir örnek promptlar |

## Bilgi Tabanı

- [CAD Adlandırma Kuralları](knowledge/cad-naming-conventions.md) — parametre, dosya, component isimleri
- [Fusion API Patterns](knowledge/fusion-api-patterns.md) — thread safety, birim dönüşümü, tuzaklar
- [Tool Tasarım Prensipleri](knowledge/tool-design-principles.md) — iyi description nasıl yazılır

## Proje Sağlığı

- [CONTRIBUTING.md](CONTRIBUTING.md) — katkı kuralları, thread safety zorunlulukları
- [SECURITY.md](SECURITY.md) — güvenlik politikası, KVKK notları, localhost guarantee
- [CHANGELOG.md](CHANGELOG.md) — sürüm geçmişi

---

## Yol Haritası

| Durum | Tool | Alan |
|-------|------|------|
| ✅ | f360_create_sketch, draw_rectangle, draw_circle | Sketch |
| ✅ | f360_extrude, fillet, shell | Features |
| ✅ | f360_set_parameter, list_parameters | Parametreler |
| ✅ | f360_export_step, export_stl | Export |
| 🔜 | f360_revolve | Features |
| 🔜 | f360_hole (ISO) | Features |
| 🔜 | f360_mirror | Features |
| 🔜 | f360_thread | Features |
| 🔜 | f360_get_mass_properties | Analiz |
| 🔜 | f360_cam_setup | CAM |

---

## Geliştirme

```bash
pip install -e ".[dev]"
python -m pytest tests/ -v        # Fusion olmadan çalışır
python -m fusion360_mcp.server    # MCP server başlat
```

Add-in: `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\fusion360_mcp_bridge`
