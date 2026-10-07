# Tasarım Felsefesi

> Bu belge başka hiçbir Fusion MCP repo'sunda yok.  
> "Neden bu firmadan alayım?" sorusunun teknik karşılığı.

---

## Bertalanffy'den Bir Sistem Teorisi

Ludwig von Bertalanffy, 1969'da *General System Theory*'sini yayımladığında biyologların, fizikçilerin ve mühendislerin aynı dili konuşması gerektiğini söylüyordu. Bir hücrenin çevre ile kurduğu alışveriş ilişkisi ile bir fabrika üretim hattının kurduğu alışveriş ilişkisi arasında derin yapısal benzerlikler vardı.

Bu proje o analojiden beslenecek şekilde tasarlandı.

---

## Dissipative Structures ve Self-Healing Pipeline

Ilya Prigogine'nin **dissipative structures** kavramı şunu söyler: denge dışı açık sistemler, dışarıdan enerji ve madde akışı aldıklarında entropi üretmek yerine yeni düzenler inşa edebilirler. Bir hücre, bir kasırga, bir alev — hepsi dissipative structure'dır.

Batch export pipeline'ı aynı şekilde çalışır:

```
Girdi: Parametre akışı (farklı çap, kalınlık, uzunluk değerleri)
Sistem: Pipeline + FusionClient + add-in
Çıktı: STEP/STL dosyaları — düzenlenmiş, adlandırılmış, tekrarlanabilir

Bozulma: Parametre başarısız → snapshot restore → sistem dengeye döner
```

`snapshot.py` ve `healing.py` (Faz 2-3) tam olarak dissipative system davranışını modelliyor: **bozulma entropi değil, denge arayışı.**

---

## Autopoiesis ve CustomEvent İzolasyonu

Maturana ve Varela'nın **autopoiesis** kavramı, canlı sistemlerin kendi sınırlarını kendilerinin çizdiğini anlatır. Bir hücre zarı hem geçirgen hem koruyucudur — içeriyi dışarıdan ayırır, ama alışverişi keser.

Fusion 360 add-in'indeki CustomEvent mimarisi bu yapıyı bilinçli olarak yansıtır:

```
Worker thread (dış dünya — TCP, MCP, LLM talepleri)
    ↕  fireCustomEvent — geçirgen ama kontrollü sınır
Main thread (Fusion iç dünyası — state, geometry, timeline)
```

Bu sınır ihlal edildiğinde — worker thread'den doğrudan `adsk.*` çağrısı — sistem çöker. Fusion'ın single-threaded mimarisi bunu zorunlu kılar. Ama biz bu zorunluluğu bir kısıt olarak değil, **temiz sınır çizme fırsatı** olarak yorumladık.

---

## Neden Bu Felsefe Pratik?

Bu sadece metafor değil, mühendislik kararlarına doğrudan yansıyor:

| Felsefi İlke | Mühendislik Kararı |
|-------------|-------------------|
| Sistem sınırları net olmalı | Her modül tek sorumluluk: `tools/` sadece FusionRequest gönderir, `adsk.*` görmez |
| Denge dışı sistemler kendi dengesini kurabilmeli | `pipeline.py`'de tek varyant başarısızlığı zinciri kesmez |
| Alışveriş kontrollü olmalı | KVKK: Forge double opt-in — her veri çıkışı bilinçli |
| Bozulmaya karşı dayanıklılık | Snapshot-before-variant: her parametre değişikliği geri alınabilir |

---

## Endüstriyel SME için Gerçek Anlam

Bir makine atölyesi bu sistemi kullandığında şunu satın almıyor:

*"Fusion 360 MCP server"*

Şunu satın alıyor:

*"Makine mühendisi saatlik çalışmasını tekrar tekrar elle yapmamanın mimarisi."*

Bertalanffy'nin söylediği şeydi bu: gerçek verimlilik, sistemin parçalarını değil, **sistemin sınırlarını ve akışlarını** optimize etmekten gelir.

---

*Bertalanffy Labs — Makine Mühendisliği × Sistem Teorisi × AI*
