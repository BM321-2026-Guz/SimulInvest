"""Varlık fiyat geçmişi ve günlük özet (issue #49): grafik + açılış / önceki kapanış / min / max.

Kaynak Yahoo Finance:
- BIST hisseleri doğrudan TL (`THYAO.IS`).
- Kripto ve altının Yahoo'da TL paritesi yok; USD fiyatı (`BTC-USD`, ons altın `GC=F`) o günün
  dolar/TL kuruyla (`USDTRY=X`) çevrilir, altın ayrıca grama bölünür. Bu yüzden canlı fiyat
  listesindeki (CoinGecko) değerden biraz farklı olabilir.
"""

import threading
import time
from bisect import bisect_right
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

import httpx

from app.errors import AppError
from app.models import AssetType
from app.services.asset_catalog import ASSETS_BY_SYMBOL, AssetInfo
from app.services.price_providers import HEADERS, TROY_OUNCE_GRAMS, YAHOO_URL

# Aralık → (Yahoo range, nokta aralığı). 5 günde saatlik, diğerlerinde günlük nokta.
RANGES = {"5d": ("5d", "60m"), "1mo": ("1mo", "1d"), "3mo": ("3mo", "1d")}
FX_SYMBOL = "USDTRY=X"
PRICE_STEP = Decimal("0.00000001")


@dataclass
class Series:
    """Yahoo'dan gelen tek bir sembolün zaman serisi (eksik değerler None olabilir)."""

    times: list[datetime]
    opens: list[float | None] = field(default_factory=list)
    closes: list[float | None] = field(default_factory=list)
    day_high: float | None = None
    day_low: float | None = None


@dataclass(frozen=True)
class PricePoint:
    time: datetime
    price: Decimal


@dataclass(frozen=True)
class History:
    symbol: str
    range: str
    open: Decimal | None
    previous_close: Decimal | None
    day_low: Decimal | None
    day_high: Decimal | None
    points: list[PricePoint]


ChartFetcher = Callable[[str, str, str], Series]  # (yahoo sembolü, range, interval) -> Series


def fetch_yahoo_chart(yahoo_symbol: str, range_: str, interval: str) -> Series:
    with httpx.Client(timeout=5.0, headers=HEADERS) as client:
        response = client.get(
            YAHOO_URL.format(symbol=yahoo_symbol), params={"range": range_, "interval": interval}
        )
        response.raise_for_status()
        result = response.json()["chart"]["result"][0]
    quote = result["indicators"]["quote"][0]
    meta = result["meta"]
    return Series(
        times=[datetime.fromtimestamp(t, UTC) for t in result.get("timestamp", [])],
        opens=quote.get("open", []),
        closes=quote.get("close", []),
        day_high=meta.get("regularMarketDayHigh"),
        day_low=meta.get("regularMarketDayLow"),
    )


def _dec(value: float | None, factor: Decimal = Decimal(1)) -> Decimal | None:
    if value is None:
        return None
    return (Decimal(str(value)) * factor).quantize(PRICE_STEP, rounding=ROUND_HALF_UP)


class _FxRate:
    """Tarihe göre dolar/TL kuru: o günün kapanışı, yoksa ondan önceki son kapanış."""

    def __init__(self, series: Series):
        pairs = sorted(
            (t.date(), Decimal(str(c)))
            for t, c in zip(series.times, series.closes, strict=False)
            if c is not None
        )
        self._dates = [d for d, _ in pairs]
        self._rates = [r for _, r in pairs]

    def on(self, day: date) -> Decimal:
        if not self._rates:
            raise ValueError("kur verisi yok")
        i = bisect_right(self._dates, day) - 1
        return self._rates[max(i, 0)]


class HistoryService:
    def __init__(self, fetch_chart: ChartFetcher = fetch_yahoo_chart, cache_seconds: int = 60):
        self._fetch = fetch_chart
        self._cache_seconds = cache_seconds
        self._cache: dict[tuple[str, str], tuple[float, History]] = {}
        self._lock = threading.Lock()

    def get(self, symbol: str, range_: str) -> History:
        asset = ASSETS_BY_SYMBOL.get(symbol.upper())
        if asset is None:
            raise AppError(404, "ASSET_NOT_FOUND", f"Varlık bulunamadı: {symbol}")
        if range_ not in RANGES:
            raise AppError(400, "INVALID_RANGE", f"Geçersiz aralık: {range_} (5d, 1mo, 3mo)")

        key = (asset.symbol, range_)
        with self._lock:
            hit = self._cache.get(key)
            if hit and hit[0] > time.monotonic():
                return hit[1]
        try:
            history = self._build(asset, range_)
        except AppError:
            raise
        except Exception:
            raise AppError(
                503, "HISTORY_UNAVAILABLE", "Fiyat geçmişi şu an alınamıyor, biraz sonra dene."
            ) from None
        with self._lock:
            self._cache[key] = (time.monotonic() + self._cache_seconds, history)
        return history

    def _build(self, asset: AssetInfo, range_: str) -> History:
        symbol, type_ = asset.symbol, asset.type
        yahoo_range, interval = RANGES[range_]
        yahoo_symbol = asset.chart_symbol  # hisse: THYAO.IS, kripto: BTC-USD, altın: GC=F
        if type_ == AssetType.GOLD:  # ons (USD) → içerdiği saf altın kadar (TL)
            scale = asset.gold_grams / TROY_OUNCE_GRAMS
        else:
            scale = Decimal(1)

        points_series = self._fetch(yahoo_symbol, yahoo_range, interval)
        # Günlük özet her zaman günlük veriden: son gün açılış, bir önceki günün kapanışı.
        daily = points_series if interval == "1d" else self._fetch(yahoo_symbol, "5d", "1d")

        if type_ == AssetType.STOCK:

            def factor(_: datetime) -> Decimal:
                return scale
        else:
            fx = _FxRate(self._fetch(FX_SYMBOL, "3mo" if range_ == "3mo" else "1mo", "1d"))

            def factor(t: datetime) -> Decimal:
                return fx.on(t.date()) * scale

        points = [
            PricePoint(t, _dec(c, factor(t)))
            for t, c in zip(points_series.times, points_series.closes, strict=False)
            if c is not None
        ]
        # Yahoo bazen açılış listesini eksik döner; o günler için açılış bilinmiyor sayılır.
        opens = daily.opens + [None] * (len(daily.times) - len(daily.opens))
        days = [
            (t, o, c)
            for t, o, c in zip(daily.times, opens, daily.closes, strict=False)
            if c is not None
        ]
        if not points or not days:
            raise ValueError("boş seri")

        last_t, last_open, _ = days[-1]
        prev = days[-2] if len(days) > 1 else None
        today = factor(last_t)
        return History(
            symbol=symbol,
            range=range_,
            open=_dec(last_open, today),
            previous_close=_dec(prev[2], factor(prev[0])) if prev else None,
            day_low=_dec(daily.day_low, today),
            day_high=_dec(daily.day_high, today),
            points=points,
        )


_service = HistoryService()


def get_history_service() -> HistoryService:
    return _service
