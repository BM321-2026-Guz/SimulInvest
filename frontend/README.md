# SimulInvest Geçici Arayüz

Backend'i uçtan uca denemek için yazılmış basit HTML/CSS/JS arayüzü. Derleme gerekmez.
Asıl frontend hazır olunca bu klasör değiştirilebilir veya silinebilir.

## Çalıştırma

1. Backend'i başlat (`backend/README.md`): `http://localhost:8000`
2. Ayrı bir terminalde repo kökünden:

```powershell
backend\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1 --directory frontend
```

3. Tarayıcıda http://127.0.0.1:5500 adresini aç.

Backend'in CORS ayarı `localhost:5500` ve `127.0.0.1:5500` adreslerine izin verir. Farklı bir API
adresi için `index.html` içinde `app.js`'ten önce `window.SIMULINVEST_API = "http://..."` tanımla.

## Ekranlar

- Giriş / kayıt (token tarayıcıda saklanır)
- Nakit, toplam değer, toplam kâr/zarar kartları
- Piyasa: "Hisse · Kripto · Altın" sekmeleri; sadece seçili grup gösterilir, seçim hatırlanır.
  BIST hisseleri (~630) 25'erli sayfalarla, sembol ya da şirket adıyla aranır (Türkçe karakterlere
  duyarsız); kripto ilk 30 coin; altında gram, çeyrek, yarım, tam ve Cumhuriyet altını.
  Satıra tıklayınca varlığın ayrıntı panosu açılır.
- Günün haberleri: piyasanın altında yer tutucu; içerik `GET /api/news` (#38) ile gelecek
- Ayrıntı panosu (#49): fiyat grafiği (5G / 1A / 3A), açılış, önceki kapanış, gün içi en düşük / en yüksek;
  haberler (menü hazır, içerik `GET /api/news` ile gelecek) ve YZ analizi için yer tutucular. Üst ve alt
  çubukla (ya da ↑ / ↓ tuşlarıyla) aynı gruptaki önceki / sonraki varlığa geçilir; `Esc` kapatır,
  "Al / Sat" düğmesi varlığı al-sat formuna seçer. Portföydeki satırlara tıklayınca da açılır.
- Al / Sat formu: varlık kutusuna yazarak arama (ör. `thyao`), nakitle alınabilecek / elde olan en fazla miktar ve `Maks` düğmesi, tahmini tutar, tam adet alınan varlıklarda (hisse, sikke altın) uyarı
- Portföy türe göre gruplu (ara toplam, değer ve kâr/zarar; türlere göre dağılım yüzdesi) ve işlem geçmişi
- 5 saniyede bir fiyat ve portföy yenilenir (`app.js` içindeki `REFRESH_MS`); sekme arka plandayken yenilenmez
