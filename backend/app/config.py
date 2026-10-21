from decimal import Decimal
from pathlib import Path

from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/.env — uygulama hangi klasörden başlatılırsa başlatılsın aynı dosya okunur.
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")

    database_url: str = "sqlite:///./simulinvest.db"
    # Varsayılanı yok: repo public olduğu için anahtar sadece .env veya ortam değişkeninden gelir.
    jwt_secret: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_expires_seconds: int = 3600
    # Login deneme sınırı: pencere içinde izin verilen hatalı deneme sayıları.
    login_max_attempts: int = 5
    login_max_attempts_per_ip: int = 20
    login_window_seconds: int = 900
    initial_balance: Decimal = Decimal("100000.00")
    price_source: str = "live"  # live | mock
    # Arka planda fiyat yenileme aralığı. CoinGecko verisi ~10-20 sn'de bir güncellendiği için
    # daha kısası fayda getirmez ve ücretsiz API sınırına (dakikada ~30 istek) yaklaştırır.
    price_cache_seconds: int = 10
    # BIST hisseleri (~630) bundan seyrek çekilir: veri Yahoo'da ~16 dk gecikmeli, 32 isteği her
    # 10 sn'de atmak yeni bilgi getirmez ve Yahoo'nun istek sınırına takılma riskini artırır.
    stock_refresh_seconds: int = 60
    cors_origins: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]


def load_settings() -> Settings:
    try:
        return Settings()
    except ValidationError as exc:
        fields = ", ".join(".".join(str(p) for p in e["loc"]).upper() for e in exc.errors())
        raise SystemExit(
            f"Ayarlar eksik veya hatalı: {fields}\n"
            f"{ENV_FILE} dosyasını oluştur (örnek: .env.example) veya ortam değişkeni olarak ver.\n"
            "JWT_SECRET en az 32 karakter olmalı. Üretmek için:\n"
            '  python -c "import secrets; print(secrets.token_hex(32))"'
        ) from None


settings = load_settings()
