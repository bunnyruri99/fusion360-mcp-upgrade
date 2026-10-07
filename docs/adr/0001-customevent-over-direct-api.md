# ADR-0001: CustomEvent Mimarisi — Doğrudan API Yerine

**Tarih:** 2026-06-06  
**Durum:** Kabul Edildi

---

## Bağlam

Fusion 360 add-in'i TCP isteklerini karşılamak için bir worker thread çalıştırıyor. Worker thread, Fusion API'sini (`adsk.fusion`, `adsk.core`) doğrudan çağırmak istedi.

Problem: Fusion 360'ın UI event loop'u single-threaded. Herhangi bir `adsk.*` çağrısı yalnızca **main UI thread'den** yapılabilir. Worker thread'den çağrı:
- Zaman zaman çalışıyormuş gibi görünüyor (race condition)
- Rastgele silent crash üretiyor
- Fusion timeline bozulabiliyor
- Autodesk dokümantasyonu bunu açıkça yasaklıyor

## Karar

`app.fireCustomEvent()` + `CustomEventHandler` mimarisi benimsendi:

1. Worker thread → `fireCustomEvent` ile event kuyruğuna mesaj bırakır
2. Fusion main thread boşta olduğunda handler'ı çalıştırır
3. Handler içinde tüm `adsk.*` çağrıları yapılır
4. `threading.Event` ile worker thread sonucu bekler

## Sonuç

**Avantajlar:**
- Thread safety garantili — Autodesk'in önerdiği yöntem
- Deterministic execution — event queue sıralı işler
- Test edilebilir — CustomEvent mock'lanabilir

**Dezavantajlar:**
- Latency artar — async dispatch + event queue bekleme (~10-50ms overhead)
- Fusion UI donuyor — uzun işlemler sırasında UI yanıt vermiyor (kabul edilebilir)
- Kod karmaşıklığı — `_pending` dict, threading.Event, UUID yönetimi gerekiyor

**Alternatiflerin neden reddedildiği:**
- `threading.Lock` + doğrudan çağrı → Fusion'ın kendi kilitleme mekanizmasıyla çelişir
- `adsk.core.Application.get()` worker'dan → bazen çalışıyor, güvenilir değil
- Subprocess/IPC → fazla overhead, değer yaratmıyor
