# SimulInvest Backend

FastAPI + SQLAlchemy + SQLite. API sözleşmesi: [`docs/openapi.yaml`](../docs/openapi.yaml).

## Kurulum (Windows)

```powershell
cd backend
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
copy .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
```

Son komutun çıktısını `.env` içindeki `JWT_SECRET=` satırına yapıştır. `JWT_SECRET` zorunludur
ve varsayılanı yoktur: tanımlı değilse veya 32 karakterden kısaysa uygulama (ve testler) başlamaz.
`.env` dosyası `.gitignore`'da, asla commit etme.

macOS / Linux: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements-dev.txt`

## Çalıştırma

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- Swagger arayüzü: http://localhost:8000/docs
- Sağlık kontrolü: http://localhost:8000/health

Dış fiyat API'leri olmadan çalışmak için `.env` içinde `PRICE_SOURCE=mock` yap.

## Test ve kod stili

```powershell
.\.venv\Scripts\python.exe -m pytest --cov=app
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format .
```

CI (`.github/workflows/backend-ci.yml`) her PR'da ruff, pytest ve en az %50 kapsam kontrolü yapar.

## Klasör yapısı

| Yol | İçerik |
|---|---|
| `app/main.py` | Uygulama, router'lar, CORS, `/health` |
| `app/config.py` | `.env` ayarları |
| `app/database.py` | Engine, session, SQLite kilit ayarı |
| `app/models.py` | Tablolar (users, wallets, holdings, transactions) |
| `app/schemas.py` | İstek/yanıt şemaları (openapi.yaml ile aynı) |
| `app/security.py` | bcrypt, JWT, `get_current_user` |
| `app/errors.py` | `{code, message}` hata formatı |
| `app/routers/` | Endpoint'ler; iş mantığı içermez |
| `app/services/` | İş mantığı: al-sat, portföy, fiyat önbelleği |
| `tests/` | pytest testleri (test-strategy.md senaryoları dahil) |

## Önemli kurallar

- Para ve miktar her yerde `Decimal`; tutarlar kuruşa yuvarlanır (ROUND_HALF_UP).
- Al-sat tek DB transaction'ında yapılır. SQLite `BEGIN IMMEDIATE` ile başlatıldığı için eşzamanlı
  iki emir bakiyeyi aynı anda okuyamaz; ayrıca DB'de `balance >= 0` kısıtı vardır.
- Hisse adedi tam sayı olmalıdır; kripto ve altında 8 ondalığa kadar izin verilir.
- Fiyatlar arka planda 10 sn'de bir yenilenir (`PRICE_CACHE_SECONDS`); istekler dış API'yi hiç beklemez,
  önbellekten okur. Yahoo'daki 12 sembol tek toplu istekle alınır. CoinGecko verisi zaten ~10-20 sn'de
  bir güncellendiği ve ücretsiz sınır dakikada ~30 istek olduğu için daha kısa aralık önerilmez.
  BIST fiyatları Yahoo'da ~15 dk gecikmelidir. Kaynak hata verirse son bilinen, o da yoksa
  `asset_catalog.py` içindeki demo fiyat kullanılır. Demo fiyat kullanılan varlıklar
  `/api/assets` yanıtında `isFallback: true` ile işaretlenir; son bilinen gerçek fiyatta bu alan
  `false` kalır ve fiyatın ne kadar eski olduğu `updatedAt` alanından anlaşılır.
- Fiyat kaynakları: BIST ve altın için Yahoo Finance, kripto için CoinGecko (anahtarsız uç noktalar).
- Login deneme sınırı: aynı IP'den aynı e-postaya 15 dakikada 5, bir IP'den toplam 20 hatalı
  deneme sonrası `429 TOO_MANY_ATTEMPTS` ve `Retry-After` başlığı döner. Sayaçlar bellekte
  tutulur, uygulama yeniden başlayınca sıfırlanır. Sınırlar `.env` ile değiştirilebilir:
  `LOGIN_MAX_ATTEMPTS`, `LOGIN_MAX_ATTEMPTS_PER_IP`, `LOGIN_WINDOW_SECONDS`.
