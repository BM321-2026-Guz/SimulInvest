"""Fiyat önbelleği (Story 1.3).

- Uygulama çalışırken fiyatlar arka planda `cache_seconds` saniyede bir yenilenir (`start()`);
  istekler dış API'yi beklemez. Arka plan çalışmıyorsa (testler) istek anında yenilenir.
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
    # True: dış kaynaktan hiç fiyat alınamadı, katalogdaki demo fiyat gösteriliyor (issue #40).
    is_fallback: bool = False


class PriceService:
    def __init__(self, fetcher: PriceFetcher, cache_seconds: int = 60):
        self._fetcher = fetcher
        self._cache_seconds = cache_seconds
        self._lock = threading.Lock()
        self._fetched_at: float | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        now = datetime.now(UTC)
        self._quotes: dict[str, Quote] = {
            a.symbol: Quote(a, a.fallback_price, now, is_fallback=True) for a in ASSETS
        }

    def _refresh(self) -> None:
        """Dış kaynaktan fiyatları çeker. Çağıran `self._lock`'u tutmalı."""
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

    def _refresh_if_stale(self) -> None:
        # Arka plan yenilemesi çalışıyorsa istekler dış API'yi hiç beklemez, önbellekten okur.
        if self.is_running and self._fetched_at is not None:
            return
        with self._lock:
            if self._fetched_at and time.monotonic() - self._fetched_at < self._cache_seconds:
                return
            self._refresh()

    # ---- arka planda yenileme ----
    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, interval: float | None = None) -> None:
        """Fiyatları `interval` saniyede bir (varsayılan: cache_seconds) arka planda yeniler."""
        if self.is_running:
            return
        wait = interval if interval is not None else self._cache_seconds
        self._stop.clear()

        def loop() -> None:
            while not self._stop.is_set():
                with self._lock:
                    self._refresh()
                self._stop.wait(wait)

        self._thread = threading.Thread(target=loop, name="price-refresh", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=10)
            self._thread = None

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
