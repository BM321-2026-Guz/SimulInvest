# SimulInvest

Yapay zeka destekli sanal borsa ve portföy simülasyonu.

BM 321 Yazılım Mühendisliği dersi dönem projesi.

## Proje Nedir?

SimulInvest, kullanıcıların gerçek para riski olmadan, kendilerine tanımlanan **100.000 TL sanal bakiye** ile Borsa (hisse), Kripto ve Altın piyasalarında alım-satım yapabildiği bir yatırım simülasyonudur. Güncel finans haberleri yapay zeka ile analiz edilerek **YÜKSELİŞ / DÜŞÜŞ** etiketiyle sunulur.

## Temel Özellikler (MVP)

- Kullanıcı kaydı, girişi ve JWT ile oturum yönetimi
- Yeni kullanıcıya otomatik 100.000 TL sanal bakiye
- Dış API'den güncel varlık fiyatları
- Al-sat işlemleri ve portföy kâr/zarar paneli

## Sonraki Aşama (P1 / P2)

- YZ haber duygu analizi (OpenAI / Gemini API)
- Varlık dağılımı pasta grafiği, izleme listesi
- Liderlik tablosu, 30 günlük fiyat grafiği

## Sistem Sınırları

Gerçek banka/kredi kartı entegrasyonu, limit/stop-loss emirleri ve WebSocket ile saniyelik fiyat akışı **kapsam dışıdır**. Uygulama yalnızca bir simülasyondur.

## Takım

| Üye | Rol |
|---|---|
| Fatma Saruhan | Product Owner & Requirements Engineer |
| Kerem Türkyılmaz | Scrum Master & Agile Process Coach |
| Özge Karaca | Lead Software Architect & Tech Lead |
| Mine Yamaner | QA & Test Automation Engineer |
| Eren Özdemir | DevOps & CI/CD Engineer |

## Dokümantasyon

- API sözleşmesi: [`docs/openapi.yaml`](docs/openapi.yaml)
- Katkı kuralları: [`CONTRIBUTING.md`](CONTRIBUTING.md)

## Teknoloji Yığını

Henüz kesinleşmedi. Karar verildiğinde burada güncellenecek.

## Kurulum ve Çalıştırma

Proje Docker ile tek komutla çalışacak şekilde hazırlanacaktır (hedef: 12. hafta).

```bash
# Hedeflenen kullanım (henüz hazır değil)
docker-compose up --build
```

## Git-Flow Özeti

- `main`: yalnızca çalışan, test edilmiş kod. Doğrudan push yasak.
- `develop`: geliştirme ana dalı.
- `feature/<konu>`: her kullanıcı hikayesi için `develop`'tan açılır, Pull Request ile `develop`'a birleşir.

Ayrıntılar için [`CONTRIBUTING.md`](CONTRIBUTING.md).

## Lisans

MIT Lisansı. Ayrıntılar için `LICENSE` dosyasına bakın.
