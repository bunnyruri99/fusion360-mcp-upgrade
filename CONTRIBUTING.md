# Katkı Rehberi

## Ortam Kurulumu

### Gereksinimler
- Python 3.11+
- Autodesk Fusion 360 (add-in testleri için)
- FreeCAD (Faz 3 testleri için, opsiyonel)

### Kurulum

```bash
git clone https://github.com/iamtechnoana/fusion360-mcp
cd fusion360-mcp
pip install -e ".[dev]"
cp .env.example .env
```

### Fusion Add-in Kurulumu

Geliştirme sırasında add-in'i her değiştirdiğinizde:

```bash
# Windows
xcopy /Y addin\fusion360_mcp_bridge\* "%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\fusion360_mcp_bridge\"

# macOS
cp -r addin/fusion360_mcp_bridge ~/Library/Application\ Support/Autodesk/Autodesk\ Fusion\ 360/API/AddIns/
```

Fusion → Tools → Add-Ins → Stop → Run (add-in'i yeniden yükler).

---

## Test Çalıştırma

```bash
# Fusion gerektirmeyen testler (her zaman çalışır)
python -m pytest tests/ -v

# Belirli modül
python -m pytest tests/test_pipeline.py -v

# Fusion add-in açıkken TCP testi
python -m pytest tests/test_smoke.py -v   # (Faz 2'de)
```

**Kural:** Her yeni tool → `tests/test_tools/test_<domain>.py` içinde en az bir test.  
**Kural:** Her yeni modül → `tests/test_<modül>.py` dosyası.

---

## Thread Safety Kuralları

Bu kurallardan herhangi birini ihlal eden PR kabul edilmez:

```
1. adsk.* çağrısı → YALNIZCA _BridgeEventHandler.notify() içinde
2. _handlers listesi → modül seviyesinde, GC koruması için ZORUNLU
3. event.wait() → timeout parametresi HER ZAMAN belirtilir
4. _pending cleanup → timeout dalında da pop() çağrılır
5. Fusion iç birimi CM → dönüşüm yalnızca mm() helper ile, tek yerden
```

---

## Yeni Tool Ekleme

1. İlgili `src/fusion360_mcp/tools/` dosyasına `ToolEntry` ekle
2. `addin/fusion360_mcp_bridge.py` `_dispatch()` fonksiyonuna handler ekle
3. Test yaz (`MockFusionClient` ile, Fusion gerektirmez)
4. `tools/CATALOG.md` güncelle
5. `CHANGELOG.md` `[Unreleased]` bölümüne ekle

Tool description 3 zorunlu element içermeli:
- **Ön koşul:** "ÖNCE X çağrılmış olmalı"
- **Birim:** mm / deg / vb.
- **Kısıt:** Sınır değer veya özel durum

Detay: [knowledge/tool-design-principles.md](knowledge/tool-design-principles.md)

---

## Commit Mesajı Formatı

```
<tip>: <kısa açıklama>

tip: feat | fix | docs | test | refactor | chore
```

Örnekler:
```
feat: f360_revolve tool — silindirik parça desteği
fix: mm() dönüşümü fillet radius'ta eksikti
docs: ADR-0003 F3D-first parallel export stratejisi
test: pipeline rollback testi eklendi
```

---

## PR Kontrol Listesi

- [ ] Testler geçiyor (`pytest tests/ -v`)
- [ ] Thread safety ihlali yok (yukarıdaki 5 kural)
- [ ] Yeni tool varsa CATALOG.md güncellendi
- [ ] CHANGELOG.md `[Unreleased]` güncellendi
- [ ] Yeni env değişkeni varsa `.env.example`'a eklendi
