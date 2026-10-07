# ADR-0002: FreeCAD Varsayılan Backend — Forge Önce Değil

**Tarih:** 2026-06-06  
**Durum:** Kabul Edildi

---

## Bağlam

Format dönüşümü (F3D → STEP/STL) için iki seçenek değerlendirildi:

**Seçenek A: Autodesk Platform Services (Forge/APS)**  
- Autodesk'in resmi cloud API'si
- F3D → STEP/OBJ/STL sunucu taraflı
- OAuth2 + API key gerekli
- Müşteri verisi Autodesk cloud'a gider

**Seçenek B: FreeCAD (yerel)**
- Açık kaynak CAD yazılımı
- Subprocess ile çalıştırılabilir
- Tamamen yerel — veri dışarı çıkmaz
- Daha sınırlı format desteği

## Karar

FreeCAD varsayılan backend olarak seçildi. Forge isteğe bağlı, consent kapılı (ADR-0005).

## Sonuç

**Neden FreeCAD önce:**

1. **KVKK riski yok** — müşteri verisi (CAD modeli) Autodesk cloud'a gitmez
2. **Bağımlılık riski yok** — Forge API değişirse sistem çalışmaya devam eder
3. **Geliştirme kolaylığı** — API key olmadan test edilebilir
4. **Endüstriyel müşteri güveni** — "verileriniz sadece sizin makinenizde"

**Forge ne zaman kullanılır:**
- Kullanıcı açıkça `forge_consent=True` verdiğinde
- FreeCAD kurulu olmadığında (fallback, consent ile)
- Forge-only formatlar gerektiğinde (Viewer SVF, vb.)

**FreeCAD dezavantajları:**
- Kurulum gerekiyor — `.env`'de `FREECAD_CMD` ayarlanmalı
- Subprocess overhead — her dönüşüm yeni process başlatır
- Bazı Fusion özellikleri FreeCAD'de eksik (parametrik geçmiş, vb.)
