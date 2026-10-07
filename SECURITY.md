# Güvenlik Politikası

## Desteklenen Sürümler

| Sürüm | Güvenlik Güncellemeleri |
|-------|------------------------|
| 0.1.x | ✅ Aktif |

---

## Güvenlik Açığı Bildirimi

Güvenlik açığı bulduysanız lütfen **public GitHub issue açmayın**.

**E-posta:** security@bertalanffylabs.com  
**Yanıt süresi:** 48 saat içinde ilk yanıt, 7 gün içinde değerlendirme

Bildiriye şunları ekleyin:
- Açıklamanın türü (RCE, veri sızıntısı, vb.)
- Etkilenen bileşen ve sürüm
- Yeniden üretme adımları
- Potansiyel etki değerlendirmesi

---

## Bu Projeye Özel Güvenlik Notları

### TCP Server — Localhost Kısıtlaması

Fusion 360 add-in TCP server **yalnızca `127.0.0.1`'e bind** edilir. Network interface'e veya `0.0.0.0`'a açılmaz.

```python
HOST = "127.0.0.1"   # addin/fusion360_mcp_bridge.py — değiştirmeyin
```

Bu değiştirilirse, yerel ağdaki herhangi bir cihaz Fusion API'sini uzaktan çalıştırabilir.

### Forge Backend — Müşteri Veri Akışı

Forge/APS backend aktif olduğunda CAD model geometrisi Autodesk cloud sunucularına iletilir. Bu:

- Ticari sır içerebilir
- KVKK / GDPR kapsamında değerlendirilebilir
- NDA ihlali riski taşıyabilir

**Varsayılan davranış: Forge devre dışı.**  
Aktifleştirmek için double opt-in gerekir ([ADR-0005](docs/adr/0005-kvkk-forge-consent-gate.md)):
1. `APS_FORGE_CONSENT=1` ortam değişkeni
2. Her çağrıda `forge_consent=True`

### Fusion API — Komut Enjeksiyonu

Add-in, MCP server'dan gelen JSON'u Fusion API parametrelerine dönüştürür. Tool şemaları Pydantic ile doğrulanır. Ancak:

- `filepath` argümanları path traversal'a karşı validate edilmez (Faz 2'de düzeltilecek)
- `name`, `unit`, `comment` gibi string argümanlar Fusion'a doğrudan iletilir

Güvenilmeyen kaynaklardan tool çağrısı yapmayın.

### Kimlik Bilgileri

Hiçbir zaman:
- API key, secret veya token kaynak koduna eklenmez
- `.env` dosyası commit edilmez
- Fusion credential'ları log'a yazılmaz

`.gitignore` `.env` ve `*.key` dosyalarını içerir.

---

## Bilinen Güvenlik Sınırlamaları

| Konu | Durum | Plan |
|------|-------|------|
| `filepath` path traversal | Çözüldü | `_validate_export_path` ile extension ve root-directory koruması eklendi |
| TCP şifreleme yok | Localhost-only, kabul edilebilir | Değişmeyecek |
| Fusion process isolation yok | Autodesk kısıtı | Değişmeyecek |
