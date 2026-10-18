# Test Stratejisi

Bu doküman, SimulInvest projesinin kalite güvencesi (QA), test seviyeleri, kullanılacak araçlar ve hedeflenen kalite metriklerini tanımlar.

## Test Katmanları

Test Piramidi (Test Pyramid) yaklaşımı benimsenerek testlerimiz üç temel katmanda kurgulanacaktır:

1. **Birim Testleri (Unit Tests):** Sistemin en küçük bağımsız fonksiyonlarını ve iş mantığını (örneğin bakiye düşme, kâr/zarar formülleri, komisyon hesaplamaları) izole ortamda dener.
2. **Entegrasyon Testleri (Integration Tests):** Farklı bileşenlerin birbiriyle uyumunu sınar. Backend API uçları ile veritabanı sorgularının ve dış servis çağrılarının birlikte doğru çalışmasını doğrular.
3. **Uçtan Uca (E2E) Testler:** Gerçek bir kullanıcının baştan sona gerçekleştirdiği iş akışlarını dener (örneğin: yeni kayıt olma → giriş yapıp JWT alma → güncel fiyatı çekme → hisse alımı yapıp portföyü güncelleme).

## Araçlar

- **Test Çerçevesi:** Python `pytest` (hızlı, modüler ve otomatik test yürütme altyapısı).
- **Kapsam Ölçümü:** `pytest-cov` (kod satırlarının ne kadarının test edildiğini denetlemek için).
- **API İstemcisi:** `httpx` / `FastAPI TestClient` (FastAPI endpoint'lerine asenkron/senkron sahte istekler atmak için).
- **Otomasyon & CI:** GitHub Actions (Eren tarafından kurulacak CI pipeline'ı üzerinde her Pull Request'te testlerin otomatik koşulması).

## Hedefler

- **Kod Kapsamı (Test Coverage):** Şartname gereğince çekirdek iş mantığında en az **%50** birim test kapsamı sağlanacaktır.
- **Sıfır Gerileme (No Regression):** PR onaylanmadan önce tüm testlerin yeşil (başarılı) yanması zorunludur.
- **Hata Yakalama Önceliği:** Bakiye hesaplamaları ve yetkisiz işlem engelleri %100 kapsama alınacaktır.

## İlk Test Senaryoları

SimulInvest MVP özellikleri için belirlenen başlangıç test senaryoları aşağıdadır:

| No | Test Senaryosu | Test Edilen Katman | Beklenen Sonuç |
|---|---|---|---|
| 1 | Bakiye yetersizken alım denenmesi | Birim / API | İşlem reddedilir, 400 Bad Request döner, bakiye değişmez. |
| 2 | Sahip olunmayan varlığın satılmaya çalışılması | Birim / API | İşlem engellenir, uygun hata mesajı döner. |
| 3 | Yeni kullanıcının başarıyla kaydolması | Entegrasyon | Kullanıcıya otomatik 100.000 TL bakiye atanır ve cüzdan oluşturulur. |
| 4 | Aynı e-posta adresiyle ikinci kez kayıt denenmesi | Entegrasyon | Kayıt reddedilir, 400 çakışma/hata kodu döner. |
| 5 | Yanlış şifre ile oturum açılmaya çalışılması | Entegrasyon | Oturum açılmaz, 401 Unauthorized hatası döner. |
| 6 | Başarılı satış işlemi sonrası portföy ve bakiye değişimi | Birim / E2E | Satılan varlık portföyden düşer, elde edilen tutar nakit bakiyeye eklenir. |
| 7 | Negatif miktarda varlık alım/satım denemesi | Birim | Doğrulama hatası fırlatılır, işlem veritabanına kaydedilmez. |


## Mevcut testler

| Senaryo | Test fonksiyonu | Durum |
|---|---|---|
| Bakiye yetersizken alım denenmesi | `test_buy_with_insufficient_balance_is_rejected` | Var |
| Sahip olunmayan varlığın satılmaya çalışılması | `test_sell_unowned_asset_is_rejected` | Var |
| Yeni kullanıcının başarıyla kaydolması | `test_register_creates_wallet_with_initial_balance` | Var |
| Aynı e-posta adresiyle kayıt denenmesi | `test_duplicate_email_is_rejected` | Var |
| Yanlış şifre ile oturum açılmaya çalışılması | `test_login_wrong_password` | Var |
| Başarılı satış işlemi sonrası portföy ve bakiye değişimi | `test_sell_updates_balance_and_holding` | Var |
| Negatif miktarda varlık alım/satım denemesi | `test_negative_or_zero_quantity_is_rejected` | Var |
