# ADR-0005: Forge Backend için Double Opt-In KVKK Kapısı

**Tarih:** 2026-06-06  
**Durum:** Kabul Edildi

---

## Bağlam

Autodesk Forge/APS backend'i kullanıldığında CAD model verisi Autodesk'in cloud sunucularına gönderilir. Bu veri:
- Müşteriye ait ticari sır içerebilir (parça geometrisi, toleranslar)
- Türkiye KVKK ve AB GDPR kapsamında kişisel veri sayılabilir (kişiselleştirilmiş ürünlerde)
- Endüstriyel müşterilerde NDA kapsamında olabilir

Varsayılan olarak Forge aktif olsaydı, kullanıcı farkında olmadan veri gönderirdi.

## Karar

Forge backend için **double opt-in** zorunlu:

1. **Sistem seviyesi:** `APS_FORGE_CONSENT=1` ortam değişkeni (sistem yöneticisi kararı)
2. **Çağrı seviyesi:** `forge_consent=True` parametresi (kullanıcı kararı)

Her iki koşul da sağlanmadan Forge HTTP çağrısı yapılmaz.

```python
# converter.py (Faz 3)
def forge_convert(filepath: str, *, forge_consent: bool = False) -> str:
    if not forge_consent:
        raise ValueError(
            "Forge backend müşteri verisini Autodesk cloud'a gönderir. "
            "forge_consent=True ile açıkça onaylayın."
        )
    if not os.getenv("APS_FORGE_CONSENT"):
        raise EnvironmentError("APS_FORGE_CONSENT=1 ortam değişkeni gerekli")
    # ...
```

## Sonuç

**Avantajlar:**
- Kullanıcı her zaman bilinçli karar alır
- KVKK / GDPR uyumu — veri aktarımı açık rıza ile
- Endüstriyel müşterilerde güven inşa eder

**Dezavantajlar:**
- Forge kullanımı daha zahmetli (iki yerde onay)
- Test ortamında `APS_FORGE_CONSENT=1` unutulursa hata üretir

**Dokümantasyon yükümlülüğü:**
- `SECURITY.md` Forge veri akışını açıkça belirtmeli
- `README.md` varsayılan backend FreeCAD olduğunu vurgulamalı
- Kullanıcıya gösterilen hata mesajı açıklayıcı olmalı (teknik kod değil)
