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
- Piyasa: BIST hisseleri, kripto ve altın ayrı kartlarda (satıra tıklayınca al-sat formuna seçilir; demo fiyatlar `demo` etiketiyle işaretlenir)
- Al / Sat formu: nakitle alınabilecek / elde olan en fazla miktar ve `Maks` düğmesi, tahmini tutar, hisse için tam sayı uyarısı
- Portföy türe göre gruplu (ara toplam, değer ve kâr/zarar; türlere göre dağılım yüzdesi) ve işlem geçmişi
- 5 saniyede bir fiyat ve portföy yenilenir (`app.js` içindeki `REFRESH_MS`); sekme arka plandayken yenilenmez
