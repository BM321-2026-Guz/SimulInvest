# DevOps Planı

## CI akışı
- GitHub Actions kullanılacak, workflow dosyaları `.github/workflows` altında olacak.
- Her Pull Request açıldığında otomatik çalışacak.
- Kod stili kontrolü yapılacak.
- Testler çalıştırılacak (pytest).
- Kod kapsam raporu üretilecek (pytest-cov, hedef en az %50).

## Güvenlik taraması
- SAST için CodeQL kullanılacak.
- Her PR'da ve main dalına birleştirmede çalışacak.
- Sonuçlar GitHub reposundaki Security sekmesinde görünecek.
- Hedef tarih: 3 Kasım.

## Docker planı
- Projeyi tek komutla (`docker-compose up`) ayağa kaldıracak yapı kurulacak.
- Backend için bir Dockerfile, servisleri birleştirmek için docker-compose.yml yazılacak.
- Final demosunda (14. hafta) proje bu şekilde çalıştırılacak.

## Gizli bilgi yönetimi
- API anahtarları ve şifreler `.env` dosyasında tutulacak.
- `.env` dosyası `.gitignore` ile repodan hariç tutulacak.
- CI içinde gereken gizli bilgiler GitHub Secrets'a konacak.
- Hiçbir anahtar veya şifre commit edilmeyecek.

## Uygulama takvimi
- 3 Kasım: SAST taraması hazır.
- 24 Kasım: CI akışı ve %50 test kapsamı hazır.
- Aralık başı (12. hafta): Docker altyapısı hazır.

Not: Teknoloji yığını şimdilik Python + FastAPI varsayımıyla yazıldı, netleşince güncellenecek.
