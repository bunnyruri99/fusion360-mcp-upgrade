# ADR-0004: Snapshot-Before-Variant Rollback Stratejisi

**Tarih:** 2026-06-06  
**Durum:** Uygulandı (Implemented)

---

## Bağlam

`pipeline.py`'de batch export sırasında bir varyant başarısız olursa Fusion design kısmen değişmiş parametrelerle kalır. Bir sonraki varyant yanlış başlangıç durumundan çalışır.

Örnek:
```
Varyant 1: outer_diameter=40, wall_thickness=3  → başarılı
Varyant 2: outer_diameter=50, wall_thickness=3  → set_parameter başarılı
                                                 → export BAŞARISIZ (timeout)
Varyant 3: outer_diameter=60, wall_thickness=3  → outer_diameter hâlâ 50!
```

## Karar

Her varyant işleminden önce parametrelerin snapshot'ı alınır. Başarısız varyant sonrası snapshot'tan restore edilir.

```python
# pipeline.py'de (Faz 2 sonrası)
async with SnapshotGuard(client) as guard:
    await set_parameters(client, spec.parameters)
    await export(client, spec.export_path)
    # hata → guard.__aexit__ parametreleri restore eder
```

## Sonuç

**Uygulama:**
```
snapshot.py:
  - take_snapshot()  → mevcut tüm user parameters'ı dict olarak al
  - restore()        → snapshot dict'ten parametreleri geri yaz
  - SnapshotGuard    → async context manager (try/finally)
```

**Avantajlar:**
- Deterministik — her varyant temiz başlangıç durumundan çalışır
- Kısmi başarı korunur — başarılı varyantlar etkilenmez
- Fusion timeline kirlenmez

**Dezavantajlar:**
- Her varyant için +1 `list_parameters` + N `set_parameter` çağrısı (restore)
- Snapshot sırasında Fusion'a başka erişim olmamalı (single-user varsayımı)

**Ne zaman snapshot almaya gerek yok:**
- Tek varyant işleniyorsa
- Parametreler read-only test ise
- Kullanıcı `rollback=False` açıkça set ettiyse
