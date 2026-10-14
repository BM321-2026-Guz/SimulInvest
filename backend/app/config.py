from decimal import Decimal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./simulinvest.db"
    # Sadece yerel geliştirme için; gerçek ortamda .env'den en az 32 baytlık değer verilmeli.
    jwt_secret: str = "yerel-gelistirme-anahtari-uretimde-degistir"
    jwt_algorithm: str = "HS256"
    jwt_expires_seconds: int = 3600
    initial_balance: Decimal = Decimal("100000.00")
    price_source: str = "live"  # live | mock
    price_cache_seconds: int = 60
    cors_origins: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]


settings = Settings()
