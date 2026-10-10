# Sprint Planı

SimulInvest projesi için sprint takvimi ve haftalık odak noktaları. Tüm teslimler **salı** günü yapılır. Plan, şartnamedeki teslimat listesine ve takımın rol dağılımına göre hazırlanmıştır.

## Sprint Takvimi

| Sprint | Hafta | Teslim tarihi | Ağırlık | Ana çıktılar |
|---|---|---|---|---|
| Sprint 1 | 4 | **13 Ekim 2026** | %15 | Öneri, vizyon, OpenAPI, RACI, repo kurulumu, backlog (8-10 hikaye) |
| Sprint 2 | 7 | **3 Kasım 2026** | %20 | SRS ve kabul kriterleri, NFR, OWASP ve SAST, Figma prototipleri |
| Sprint 3 | 10 | **24 Kasım 2026** | %25 | C4 ve UML dokümanı, çalışan MVP, CI ve %50 test kapsamı |
| Final | 13-14 | **15 veya 22 Aralık 2026** | %40 | Docker ile canlı ürün, E2E test raporu, statik analiz raporu, demo |

> Final tarihi sınıf içi sunum programına göre kesinleşecek. 8. hafta vize haftasıdır, iş yükü bilinçli olarak hafif tutulmuştur.

## Haftalık Plan

| Hafta | Bitiş | Odak | Öne çıkan işler |
|---|---|---|---|
| 4 | 13 Eki | **Sprint 1 kapanışı** | Kullanıcı hikayeleri ve issue'lar, ERD, test stratejisi, DevOps planı, RACI, sprint planı |
| 5 | 20 Eki | Gereksinimler ve iskelet | SRS taslağı, kabul kriterleri, FastAPI proje iskeleti, ortam kurulumu (Python, venv) |
| 6 | 27 Eki | Kalite ve güvenlik | NFR ve SLA/SLO taslağı, OWASP analizi, kayıt ve giriş (JWT), Figma ekranları |
| 7 | 3 Kas | **Sprint 2 teslimi** | SRS, NFR, OWASP ve CodeQL, Figma prototipi ve user flow |
| 8 | 10 Kas | Vize haftası | Hafif iş: cüzdan ve fiyat servisi araştırması |
| 9 | 17 Kas | MVP geliştirme | Al-sat mantığı, portföy, frontend ekranlarını API'ye bağlama, birim testler |
| 10 | 24 Kas | **Sprint 3 teslimi** | C4 ve UML, MVP, CI pipeline, %50 kapsam |
| 11 | 1 Ara | Test ve düzeltme | E2E testler, hata düzeltme, PR akışı |
| 12 | 8 Ara | Docker ve kalite | docker-compose, refactoring, statik analiz raporu |
| 13-14 | 15 / 22 Ara | **Final** | Demo provası, sunum, mimari savunma hazırlığı |

## Sprint 1 Kalan İşler

| İş | Sorumlu | Durum |
|---|---|---|
| Repo, README, .gitignore, lisans, Git-Flow, branch koruması | Kerem, Eren | Tamam |
| Taslak OpenAPI (`docs/openapi.yaml`) | Özge | Taslak hazır |
| Kullanıcı hikayeleri (8-10), Story Point ve kabul kriterleri | Fatma | Devam ediyor |
| Hikayelerin issue olarak açılması, etiket, milestone, GitHub Projects panosu | Fatma, Kerem | Başlanmadı |
| ERD taslağı | Özge | Başlanmadı |
| Test stratejisi | Mine | Başlanmadı |
| DevOps planı | Eren | Başlanmadı |
| RACI matrisi (`docs/raci.md`) | Kerem | Hazır, yüklenecek |
| Proje öneri ve sistem vizyonu dokümanları | Kerem | Yüklenecek |

## Haftalık Çalışma Düzeni

- **Pazartesi:** Kısa durum mesajı. Herkes bu hafta ne yapacağını yazar.
- **Perşembe:** Engelleyici kontrolü. Takılan varsa Scrum Master'a bildirilir.
- **Salı (sprint sonu):** Teslim ve kısa retrospektif (ne iyi gitti, ne düzelecek).
- Her iş bir issue'dur ve `feature/` dalında PR ile teslim edilir.

## Teknoloji Yığını (Onay Bekliyor)

| Katman | Seçim |
|---|---|
| Backend | Python, FastAPI |
| Veritabanı | SQLite (SQLAlchemy) |
| Frontend | HTML, CSS, JavaScript |
| Test | pytest, pytest-cov |
| CI ve güvenlik | GitHub Actions, CodeQL |
| Konteyner | Docker, docker-compose |

## Riskler

| Risk | Önlem |
|---|---|
| Dış fiyat API'si (yfinance, CoinGecko) kesintisi veya kırılması | Önbellek ve demo için yedek (mock) veri |
| Ekip deneyimi sınırlı | Küçük, net görevler; takılanlar için doğrudan destek |
| Kodlamanın geç başlaması | 5. haftadan itibaren dokümanla paralel iskelet kod |
| PR incelemelerinin tek kişiye yığılması | Müsait değilse Kerem inceleyici olur |
