# fusion360-mcp

**Fusion 360 API over MCP protocol — Bertalanffy Labs**

Autodesk Fusion 360'ı herhangi bir MCP-uyumlu AI client'tan (Claude Code, Cursor, Codex) doğal dille kontrol edin.

```
Any MCP Client ──(stdio/JSON-RPC)──► MCP Server ──(TCP :9876)──► Add-in ──(CustomEvent)──► Fusion Main Thread
     Claude Code                   fusion360_mcp               Fusion 360 API
```

---

## Ön Koşullar

| Gereksinim | Versiyon |
|-----------|----------|
| Autodesk Fusion 360 | 2.0.19800+ |
| Python | 3.11+ |
| İşletim Sistemi | Windows 10/11, macOS 13+ |

---

## Kurulum

### 1. Python paketini kur

```bash
git clone https://github.com/iamtechnoana/fusion360-mcp
cd fusion360-mcp
pip install -e ".[dev]"
```

### 2. Ortam değişkenlerini ayarla

```bash
cp .env.example .env
# .env dosyasını düzenle (varsayılanlar genellikle yeterli)
```

### 3. Fusion 360 add-in'i kur

```
addin/fusion360_mcp_bridge/ klasörünü kopyala:

Windows: %APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\
macOS:   ~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/AddIns/
```

Fusion 360 → **Tools → Add-Ins → Add-Ins** (Shift+S) → `fusion360_mcp_bridge` → **Run**

Ekranda `"Fusion MCP bridge started — listening on port 9876"` görünmeli.

### 4. Claude Code'a bağla

```bash
claude mcp add fusion360 --scope project -- python -m fusion360_mcp.server
```

ya da `.mcp.json` dosyası proje kökünde hazır — Claude Code otomatik algılar.

---

## İlk Test

```bash
# Add-in çalışıyor mu?
python -c "
import socket, json
s = socket.create_connection(('127.0.0.1', 9876), timeout=3)
s.sendall(b'{\"tool\":\"list_parameters\",\"args\":{}}\n')
import time; time.sleep(0.5)
print(s.recv(1024).decode())
s.close()
"
```

Beklenen çıktı: `{"success": true, "message": "0 parameters found", "data": {}}`

---

## Tool Listesi

| Tool | İşlev |
|------|-------|
| `f360_create_sketch` | Yeni sketch aç (XY/XZ/YZ) |
| `f360_draw_rectangle` | Dikdörtgen çiz (mm) |
| `f360_draw_circle` | Daire çiz (mm) |
| `f360_extrude` | Profili 3D solid'e extrude et |
| `f360_revolve` | Profili eksende döndür (şaft, flanş) |
| `f360_fillet` | Kenar yuvarlatma |
| `f360_shell` | Gövdeyi boşalt (housing/enclosure) |
| `f360_hole` | Delik aç (through/blind) |
| `f360_hole_pattern` | Bolt circle delik dizisi |
| `f360_create_parameter` | Yeni user parameter oluştur |
| `f360_set_parameter` | User parameter güncelle → rebuild |
| `f360_list_parameters` | Tüm parametreleri listele |
| `f360_export_step` | STEP export (supplier/CNC) |
| `f360_export_stl` | STL export (3D print) |

Tam dokümantasyon: [docs/tools/](docs/tools/)

---

## Batch Export (Parametrik Varyant Üretimi)

```python
from fusion360_mcp.pipeline import generate_variants, VariantSpec
from fusion360_mcp.fusion.client import FusionClient

client = FusionClient("127.0.0.1", 9876, timeout=30)
variants = [
    VariantSpec({"outer_diameter": d}, f"exports/flange_OD{d}.step")
    for d in [40, 50, 60, 70, 80]
]
report = await generate_variants(client, variants)
print(report.summary())
```

---

## Bilinen Kısıtlar

- **Fusion iç birimi CM** — tüm kullanıcı değerleri mm, dönüşüm add-in içinde otomatik
- **Tool'lar sıralı çalışır** — MCP client tarafında Fusion çağrıları serialize edilir; her tool call ayrı TCP bağlantısı
- **30 saniyelik timeout** — karmaşık CAM operasyonları aşabilir
- **Main thread zorunlu** — Fusion API worker thread'den çağrılamaz (CustomEvent mimarisi bu yüzden)
- `runOnStartup: false` — Fusion her açılışta add-in'i manuel başlatmayı gerektirir

Detaylar: [docs/known-issues.md](docs/known-issues.md)

---

## Geliştirme

```bash
python -m pytest tests/ -v          # Fusion olmadan çalışır
python -m fusion360_mcp.server      # MCP server başlat
```

## Katkı & Lisans

Katkı rehberi: [CONTRIBUTING.md](CONTRIBUTING.md)  
Güvenlik bildirimi: [SECURITY.md](SECURITY.md)

---

## Nguồn Tham Khảo & Ghi Nhận (Credits & Attribution)

Dự án này được phát triển, nâng cấp bảo mật và tối ưu hóa tính ổn định dựa trên mã nguồn gốc của:
- **Tác giả gốc**: [iamtechnoana](https://github.com/iamtechnoana) / **Bertalanffy Labs**
- **Kho lưu trữ gốc**: [iamtechnoana/fusion360-mcp](https://github.com/iamtechnoana/fusion360-mcp)

### Các cải tiến & bản vá trong phiên bản nâng cấp này:
1. **Bảo mật**: Khắc phục lỗ hổng Path Traversal (`_validate_export_path`), giới hạn payload TCP (64 KB), danh sách trắng đơn vị đo lường (unit whitelist) cho parameters.
2. **Độ ổn định**: Sửa lỗi `UnboundLocalError` trong event handler CustomEvent, bắt lỗi `OSError` trong vòng lặp TCP server, kẹp giá trị timeout tối thiểu (`req_timeout`).
3. **Tính năng mới**: Bổ sung công cụ kiểm tra sức khỏe hệ thống `f360_ping` và cơ chế hoàn tác tham số giao dịch tự động `SnapshotGuard` (theo ADR-0004).
4. **Tương thích MCP**: Khóa phiên bản MCP SDK `<2` và cấu hình sẵn sàng cho Claude Desktop, Cursor, và Codex.

---

## Lisans

MIT — Bertalanffy Labs © 2026 / Upgraded & Enhanced Edition

