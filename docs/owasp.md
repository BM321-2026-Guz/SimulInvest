# OWASP Top 10 Risk Analizi (SimulInvest)

## 1. Genel bakış
OWASP Top 10 (2025), web uygulamalarındaki en kritik 10 güvenlik riskini listeler. Bu belge SimulInvest backend'ini (FastAPI) bu başlıklara göre değerlendirir.
Kaynak: https://owasp.org/Top10/

## 2. Top 10 ve SimulInvest
| No | Başlık | Tek cümleyle ne demek | SimulInvest'te ilgili mi? |
|---|---|---|---|
| A01 | Broken Access Control | Kullanıcı yetkisi olmayan veriye ya da işleme erişebilir. | Evet: bir kullanıcı başkasının portföyünü ve işlemlerini görmemeli. Her istekte JWT'deki kullanıcıya göre filtreleniyor; testi var (test_users_cannot_see_each_others_data). |
| A02 | Security Misconfiguration | Sistem güvensiz varsayılan ayarlarla ya da yanlış yapılandırmayla çalışır. | Evet: JWT anahtarı artık zorunlu (varsayılan yok), CORS yalnızca localhost:5500'e açık. Docker/proxy arkasında IP okuma ayarı ileride gözden geçirilmeli. |
| A03 | Software Supply Chain Failures | Uygulamanın kullandığı üçüncü taraf kütüphaneler, bağımlılıklar veya CI/CD süreçlerindeki güvenlik zafiyetleridir. | Evet: `requirements.txt` içindeki kütüphanelerin sürümleri sabitlenmeli, Dependabot takibi yapılmalı ve GitHub Actions adımları güncel tutulmalıdır. |
| A04 | Cryptographic Failures | Hassas verilerin yetersiz, zayıf veya yanlış şifreleme yöntemleriyle korunması durumudur. | Evet: Parolalar bcrypt ile hash'leniyor, JWT HS256 ile imzalanıyor ve gizli anahtar zorunlu tutuluyor; yerel geliştirmede ise henüz HTTPS yok. |
| A05 | Injection | Güvenilmeyen kullanıcı girdilerinin sorgu veya komut olarak çalıştırılarak sistemin kötüye kullanılmasıdır. | Evet: Veritabanı sorguları SQLAlchemy ORM ile parametreli yapıldığı için SQL enjeksiyonu önleniyor; arayüzde XSS ve token'ın localStorage'da saklanması risk oluşturuyor. |
| A06 | Insecure Design | Kodlama hatalarından ziyade sistem mimarisi ve tasarım aşamasındaki güvenlik eksiklikleridir. | Evet: Fiyat verisinin dış API'ye bağımlı olması (kesintide demo fiyat gösterilmesi) ve deneme sınırının bellekte tutulması gibi tasarım kararlarını kapsar. |
| A07 | Authentication Failures | Kullanıcı kimlik doğrulama, oturum yönetimi ve parola politikalarındaki yetersizliklerdir. | Evet: Giriş deneme sınırı (15 dakikada 5 hatalı deneme), 8-72 karakter parola kuralı ve 1 saatlik JWT süresi ile doğrudan ilgilidir. |
| A08 | Software or Data Integrity Failures | Kodun veya kritik verilerin doğrulanmadan işlenmesi ve bütünlüğünün bozulmasıdır. | Evet: `main`/`develop` dallarının korumalı olması, PR onay/test zorunluluğu ve bakiye eksiye düşememe kuralı veri bütünlüğünü sağlar. |
| A09 | Security Logging & Alerting Failures | Şüpheli durumların ve güvenlik ihlallerinin loglanmaması veya zamanında fark edilememesidir. | Evet: Hatalı giriş denemelerinin ve kritik güvenlik olaylarının `auth.py` ile `login_limiter.py` üzerinde loglanması ve izlenmesi gerekir. |
| A10 | Mishandling of Exceptional Conditions | Sistemde oluşan hataların ve istisnaların güvensiz veya tutarsız şekilde ele alınmasıdır. | Evet: `errors.py` ile hataların standart yanıt dönmesi ve dış fiyat kaynağı çöktüğünde uygulamanın kilitlenmeyip yedek fiyata geçmesi bu kapsamdadır. |
