# DevOps Planı

## CI akışı
- GitHub Actions kullanılıyor, workflow dosyaları `.github/workflows` altında (`backend-ci.yml`, `codeql.yml`).
- Her Pull Request'te ve `develop` / `main` push'unda otomatik çalışır.
- Kod stili kontrolü yapılır (ruff check ve ruff format --check).
- Testler çalışır (pytest).
- Kod kapsamı ölçülür (pytest-cov); en az %50 altında CI kırmızı olur.
- Testlerde `JWT_SECRET` her çalıştırmada rastgele üretilir, repoda sabit değer yoktur.
- `main` ve `develop` dallarında `test` ve `analyze` kontrolleri zorunludur.

## Güvenlik taraması
- SAST için CodeQL (Python) kullanılıyor.
- Her PR'da ve `develop` / `main` push'unda çalışır.
- Sonuçlar GitHub reposundaki Security sekmesinde görünür.
- Hedef tarih: 3 Kasım (çalışıyor, bulgular OWASP raporunda değerlendirilecek).

## Docker planı
- Projeyi tek komutla (`docker-compose up`) ayağa kaldıracak yapı kurulacak.
- Backend için bir Dockerfile, servisleri birleştirmek için docker-compose.yml yazılacak.
- Final demosunda proje bu şekilde çalıştırılacak.

## Gizli bilgi yönetimi
- API anahtarları ve şifreler `.env` dosyasında tutulacak.
- `.env` dosyası `.gitignore` ile repodan hariç tutulacak.
- CI içinde gereken gizli bilgiler GitHub Secrets'a konacak.
- `JWT_SECRET` zorunludur ve varsayılanı yoktur; yoksa uygulama başlamaz (örnek: `backend/.env.example`).
- Hiçbir anahtar veya şifre commit edilmeyecek.

## Uygulama takvimi
- 3 Kasım: SAST taraması hazır (CodeQL çalışıyor).
- 24 Kasım: CI akışı ve %50 test kapsamı hazır.
- Aralık başı (12. hafta): Docker altyapısı hazır.
- Aralık başı: SonarQube raporu hazır.


## Statik kod analizi (SonarQube)
- Final teslimi için statik analiz raporu hazırlanacak.
- CodeQL güvenlik açıklarını, SonarQube ise kod kalitesini ölçecek (hata, kod kokusu, tekrar eden kod, test kapsamı).
- Repo Public olduğu sürece SonarCloud kullanılacak, GitHub Actions içinde PR ve develop push'unda çalışacak.
- Repo Private olursa SonarQube Community sürümü Docker ile yerelde çalıştırılacak.
- Rapor için panel ekran görüntüsü ve kalite kapısı (quality gate) sonucu alınacak.
