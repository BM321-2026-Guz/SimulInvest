
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

## 3. Bulgular

| # | Bulgu | OWASP 2025 | Durum |
|---|---|---|---|
| B1 | JWT için varsayılan gizli anahtar vardı | A04 Cryptographic Failures, A02 Security Misconfiguration | Düzeltildi (PR #24) |
| B2 | Girişte deneme sınırı yoktu | A07 Authentication Failures | Düzeltildi (PR #45) |
| B3 | Yanıt süresinden e-postanın kayıtlı olup olmadığı anlaşılabilir (timing attack) | A07 Authentication Failures | Açık |
| B4 | Kayıtta "e-posta zaten kayıtlı" mesajı e-postayı ele veriyor | A07 Authentication Failures | Bilinçli ödün |
| B5 | Deneme sınırı Docker/proxy arkasında herkesi aynı IP görür | A02 Security Misconfiguration | Açık |
| B6 | Token tarayıcının localStorage'ında (XSS ile çalınabilir) | A05 Injection, A07 Authentication Failures | Açık |
| B7 | JWT 1 saat geçerli, çıkışta iptal yok | A07 Authentication Failures | Kabul edilen risk |
| B8 | Fiyatlar dış API'ye bağlı, kesintide demo fiyat gösteriliyor | A06 Insecure Design, A10 Mishandling of Exceptional Conditions | Azaltıldı (PR #45, #46) |
| B9 | CORS yalnızca localhost:5500'e izinli | A02 Security Misconfiguration | İyi |
| B10 | Parola kuralı 8-72 karakter | A07 Authentication Failures | Yeterli |
| B11 | Bağımlılık güncellemeleri (Dependabot) | A03 Software Supply Chain Failures | Takip |
| B12 | HTTPS ve güvenlik başlıkları yok | A02 Security Misconfiguration | Yerel demo |

### Bulgu Detayları (Risk / Etki / Çözüm / Durum)

#### B3. Yanıt Süresinden E-posta Tespiti (Timing Attack)
- **Risk:** Kullanıcı giriş veya kayıt yanıt sürelerinin farkından sistemde e-postanın varlığının tespit edilmesi.
- **Etki:** Saldırganların geçerli kullanıcı e-postalarını listelemesine olanak tanır.
- **Çözüm:** Yanıt sürelerini sabitlemek için sabit zamanlı karşılaştırma/işlem yapmak.
- **Durum:** Açık

#### B5. Proxy/Docker Arkasında Yanlış IP Tespiti
- **Risk:** Rate limiting mekanizmasının proxy arkasından gelen isteklerde gerçek IP yerine proxy IP'sini okuması.
- **Etki:** Tek bir kullanıcının engellenmesi durumunda tüm ağın veya proxy arkasındaki tüm kullanıcıların engellenmesi.
- **Çözüm:** `X-Forwarded-For` başlığını doğru yapılandırıp gerçek istemci IP'sini okumak.
- **Durum:** Açık

#### B6. JWT Token'ın LocalStorage'da Saklanması
- **Risk:** XSS zafiyeti oluşması durumunda zararlı betiklerin localStorage'a erişebilmesi.
- **Etki:** Kullanıcı oturumunun (JWT token) çalınması.
- **Çözüm:** Token'ları `HttpOnly` ve `SameSite` bayrakları aktif olan çerezlerde (cookies) saklamak.
- **Durum:** Açık

## 4. SAST (Statik Kod Analizi) Değerlendirmesi

Projeye uygulanan statik güvenlik taraması (SAST) sonuçları ve OWASP 2025 standartlarına göre yapılan değerlendirme aşağıdadır:

- **B3 (Timing Attack):** Giriş ve kayıt servislerinde yanıt sürelerindeki milisaniyelik farklar, e-postanın veritabanında var olup olmadığını açık etmektedir. Sabit zamanlı karşılaştırma algoritmaları veya yapay gecikme (padding) eklenmelidir.
- **B5 (Proxy / IP Tespiti):** `login_limiter.py` servisi doğrudan istemci IP'sine dayanmaktadır. Uygulama Docker veya Reverse Proxy arkasında çalıştığında tüm istekler tek IP olarak görülebilir. `X-Forwarded-For` başlığı güvenli bir şekilde işlenmelidir.
- **B6 (XSS & LocalStorage):** JWT token'larının browser `localStorage` alanında saklanması, muhtemel bir XSS zafiyetinde token'ın çalınmasına yol açabilir. Çözüm olarak token'ların `HttpOnly`, `Secure` ve `SameSite` çerezlerinde saklanması önerilir.
- **B10 (Parola Politikası):** Parola uzunluğunun 8-72 karakter arasında kısıtlanması temel düzeyde yeterli olsa da, OWASP A07 standartlarına uyum için parola karmaşıklığı ve sızdırılmış parola (pwned passwords) kontrolleri entegre edilmelidir.
