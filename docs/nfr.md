# Fonksiyonel Olmayan Gereksinimler (NFR)

| Ölçüt | Hedef | Nasıl Ölçülür |
|---|---|---|
| Yanıt Süresi | API isteklerinin %95'i 500 ms'nin altında yanıt verir. | Postman/pytest ile süre ölçümü|
| Doğruluk | Para hesaplarında ondalık hatası olmaz. | Decimal veri tipi kullanımı, birim testleri |
| Güvenlik | Parolalar hash'lenerek saklanır, asla düz metin olarak saklanmaz. | Kod incelemesi, hash kontrol testi |
| Test Kapsamı | En az %50 kod kapsamı sağlanır. | pytest-cov raporu (CI) |
| Taşınabilirlik | Proje tek komutla ayağa kalkar. | 'docker-compose up' komut testi |
| Bakım Kolaylığı | Kod stili kuralları CI'da otomatik denetlenir. | ruff kontrolü (CI) |
| Veri Tutarlılığı | Yetersiz bakiye veya hatalı alım-satımda bakiye değişmez.| Veritabanı kontrolü ve entegrasyon testleri |
| Kesintisiz Çalışma | API hataları sistemi çökertmez. | Yedek veri mekanizması testi |
