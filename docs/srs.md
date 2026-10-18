# Yazılım Gereksinim Belirtimi (SRS)
## 1. Giriş
Amaç: Bu belge SimulInvest sisteminin ne yapacağını tanımlar.
Kapsam: Gerçek para riski olmadan Borsa, Kripto ve Altın alım-satımı simülasyonu.

## 2. Genel tanım
Kullanıcı tipi: Bireysel yatırım simülasyonu kullanıcısı.
Kısıt: Uygulama yalnızca simülasyondur, gerçek para yoktur.

## 3. Fonksiyonel gereksinimler
| No | Gereksinim | İlgili hikaye |
| --- | --- | --- |
| FR-1 | Sistem e-posta ve şifre ile kayıt ve girişe izin vermelidir. | Story 1.1 |
| FR-2 | Yeni kullanıcıya otomatik 100.000 TL bakiye verilmelidir. | Story 1.1 |
| FR-3 | Sistem güncel varlık fiyatlarını göstermelidir. | Story 1.3 |
| FR-4 | Yeterli bakiye ile alım-satım yapılabilmeli ve portföy kâr/zarar izlenebilmelidir. | Story 1.4 |
| FR-5 | Finans haberleri YZ etiketleriyle (YÜKSELİŞ/DÜŞÜŞ) listelenmelidir. | Story 2.1 |
| FR-6 | Portföy varlık dağılımı pasta grafiği ile gösterilmelidir. | Story 2.2 |
| FR-7 | Kullanıcılar istedikleri varlıkları izleme listesine ekleyip çıkarabilmelidir. | Story 2.3 |
| FR-8 | Kullanıcılar portföy değerlerine göre liderlik tablosunda sıralanmalıdır. | Story 3.1 |
| FR-9 | Seçilen varlığın son 30 günlük fiyat geçmişi çizgi grafikte gösterilmelidir. | Story 3.2 |

## 4. Kapsam dışı
Gerçek banka entegrasyonu, limit/stop-loss emirleri, WebSocket ile saniyelik fiyat.
