# ADR-0003: F3D-First Paralel Export Stratejisi

**Tarih:** 2026-06-06  
**Durum:** Planlandı (Faz 3)

---

## Bağlam

Batch export pipeline'ı (`pipeline.py`) şu an her varyant için:
1. Parametreleri güncelle
2. STEP/STL export et

Bu sıralı çalışır. 10 varyant × 30 saniye = 5 dakika.

Paralel export için iki strateji değerlendirildi:

**Strateji A: Doğrudan Paralel Export**  
Her varyant için aynı anda `set_parameter` + `export` çalıştır.  
Problem: Fusion single-design, tek parametrik durum. Paralel parametre değişikliği tutarsızlık üretir.

**Strateji B: F3D-First**  
1. Her varyant için F3D (Fusion'ın native formatı) kaydet → snapshot
2. F3D'leri worker pool'da paralel dönüştür (FreeCAD/Forge)

## Karar

F3D-First stratejisi benimsendi.

## Sonuç

**Neden F3D-First:**

1. **Atomik rollback** — her snapshot bağımsız, parametre karışmaz
2. **Gerçek paralellik** — dönüşüm Fusion dışında, CPU core başına bir worker
3. **Hata izolasyonu** — bir varyant dönüşümü başarısız olursa diğerleri etkilenmez
4. **Cache** — aynı F3D varsa tekrar Fusion'a dokunma (`cache_manager.py`)

**Uygulama sırası (Faz 3):**
```
pipeline.py (Faz 2, mevcut):
  set_parameter → export_step (sıralı, Fusion içi)

pipeline.py (Faz 3, F3D-First):
  for each variant:
    set_parameter → export_f3d → snapshot_store
  parallel_export_pool:
    for each f3d in snapshots:
      freecad_convert(f3d, "step") → output
```

**Dezavantajlar:**
- F3D dosyaları disk alanı kullanır → `cache_manager.py` TTL ile temizler
- Fusion F3D export API'si ek complexity ekler
- FreeCAD F3D import bazen eksik özellikler içeriyor
