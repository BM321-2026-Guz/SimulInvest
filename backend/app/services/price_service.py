"""Fiyat önbelleği (Story 1.3).

- Fiyatlar en fazla `cache_seconds` saniye eskidir.
- Dış kaynak hata verirse son bilinen fiyat, o da yoksa katalogdaki yedek fiyat kullanılır;
  uygulama hiçbir koşulda fiyat yüzünden çökmez.
"""

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from app.config import settings
from app.services.asset_catalog import ASSETS, ASSETS_BY_SYMBOL, AssetInfo
from app.services.price_providers import fetch_live_prices

log = logging.getLogger(__name__)

PriceFetcher = Callable[[], dict[str, Decimal]]
PRICE_STEP = Decimal("0.00000001")


@dataclass(frozen=True)
class Quote:
    asset: AssetInfo
    price: Decimal
    updated_at: datetime


class PriceService:
    def __init__(self, fetcher: PriceFetcher, cache_seconds: int = 60):
        self._fetcher = fetcher
        self._cache_seconds = cache_seconds
        self._lock = threading.Lock()
        self._fetched_at: float | None = None
        now = datetime.now(UTC)
        self._quotes: dict[str, Quote] = {a.symbol: Quote(a, a.fallback_price, now) for a in ASSETS}

    def _refresh_if_stale(self) -> None:
        with self._lock:
            if self._fetched_at and time.monotonic() - self._fetched_at < self._cache_seconds:
                return
            try:
                fresh = self._fetcher()
            except Exception as exc:
                log.warning("Fiyatlar yenilenemedi, eski/yedek fiyatlar kullanılıyor: %s", exc)
                fresh = {}
            now = datetime.now(UTC)
            for symbol, price in fresh.items():
                asset = ASSETS_BY_SYMBOL.get(symbol)
                if asset and price > 0:
                    rounded = price.quantize(PRICE_STEP, rounding=ROUND_HALF_UP)
                    self._quotes[symbol] = Quote(asset, rounded, now)
            self._fetched_at = time.monotonic()

    def get_all(self) -> list[Quote]:
        self._refresh_if_stale()
        return [self._quotes[a.symbol] for a in ASSETS]

    def get(self, symbol: str) -> Quote | None:
        self._refresh_if_stale()
        return self._quotes.get(symbol.upper())


def _no_fetch() -> dict[str, Decimal]:
    return {}


_service = PriceService(
    fetch_live_prices if settings.price_source == "live" else _no_fetch,
    settings.price_cache_seconds,
)


def get_price_service() -> PriceService:
    return _service
