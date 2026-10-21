"""Dış fiyat kaynakları. Her fonksiyon {sembol: TL fiyatı} döner; alamadığı sembolü atlar."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal

import httpx

from app.config import settings
from app.models import AssetType
from app.services.asset_catalog import ASSETS

log = logging.getLogger(__name__)

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
# Tek istekte birden çok sembol; Yahoo en fazla 20 sembol kabul ediyor (21+ → HTTP 400).
YAHOO_BATCH_URL = "https://query1.finance.yahoo.com/v7/finance/spark"
YAHOO_BATCH_SIZE = 20
YAHOO_PARALLEL = 6  # ~630 hisse = 32 istek; 6 paralel istekle ~1-2 sn
# Toplu istekte eksik kalanlar tek tek denenir; çok eksik varsa Yahoo zaten sorunludur,
# yüzlerce tek istek atmak yerine o tur atlanır (son bilinen fiyat kullanılır).
MAX_SINGLE_RETRIES = 20
GOLD_SYMBOLS = ("GC=F", "USDTRY=X")  # ons altın (USD) ve dolar/TL
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
TROY_OUNCE_GRAMS = Decimal("31.1034768")
# Yahoo, tarayıcı olmayan istemcileri User-Agent olmadan reddediyor.
HEADERS = {"User-Agent": "Mozilla/5.0 (SimulInvest ders projesi)"}


def _yahoo_price(client: httpx.Client, yahoo_symbol: str) -> Decimal:
    response = client.get(YAHOO_URL.format(symbol=yahoo_symbol), params={"range": "1d"})
    response.raise_for_status()
    meta = response.json()["chart"]["result"][0]["meta"]
    return Decimal(str(meta["regularMarketPrice"]))


def _yahoo_batch(client: httpx.Client, yahoo_symbols: list[str]) -> dict[str, Decimal]:
    """En fazla 20 sembollük tek toplu istek; hata olursa boş döner."""
    try:
        response = client.get(
            YAHOO_BATCH_URL,
            params={"symbols": ",".join(yahoo_symbols), "range": "1d", "interval": "1d"},
        )
        response.raise_for_status()
        results = response.json()["spark"]["result"] or []
    except Exception as exc:
        log.warning("Yahoo toplu fiyat isteği başarısız (%d sembol): %s", len(yahoo_symbols), exc)
        return {}
    prices = {}
    for item in results:
        try:
            meta = item["response"][0]["meta"]
            prices[item["symbol"]] = Decimal(str(meta["regularMarketPrice"]))
        except (KeyError, IndexError, TypeError):
            continue
    return prices


def fetch_yahoo(client: httpx.Client, yahoo_symbols: list[str]) -> dict[str, Decimal]:
    """Sembolleri 20'şerli paketlere bölüp paralel ister; eksik kalan birkaçını tek tek dener."""
    chunks = [
        yahoo_symbols[i : i + YAHOO_BATCH_SIZE]
        for i in range(0, len(yahoo_symbols), YAHOO_BATCH_SIZE)
    ]
    quotes: dict[str, Decimal] = {}
    with ThreadPoolExecutor(max_workers=min(YAHOO_PARALLEL, max(len(chunks), 1))) as pool:
        for part in pool.map(lambda chunk: _yahoo_batch(client, chunk), chunks):
            quotes.update(part)

    missing = [s for s in yahoo_symbols if s not in quotes]
    if len(missing) > MAX_SINGLE_RETRIES:
        log.warning("Yahoo'dan %d sembolün fiyatı gelmedi; bu tur tek tek denenmiyor", len(missing))
        return quotes
    for yahoo_symbol in missing:
        try:
            quotes[yahoo_symbol] = _yahoo_price(client, yahoo_symbol)
        except Exception as exc:  # tek bir sembolün hatası diğerlerini engellemesin
            log.warning("Yahoo fiyatı alınamadı (%s): %s", yahoo_symbol, exc)
    return quotes


def fetch_stocks(client: httpx.Client) -> dict[str, Decimal]:
    stocks = {a.source_id: a.symbol for a in ASSETS if a.type == AssetType.STOCK}
    quotes = fetch_yahoo(client, list(stocks))
    return {symbol: quotes[ysym] for ysym, symbol in stocks.items() if ysym in quotes}


def fetch_gold(client: httpx.Client) -> dict[str, Decimal]:
    quotes = fetch_yahoo(client, list(GOLD_SYMBOLS))
    if not all(s in quotes for s in GOLD_SYMBOLS):
        return {}
    ounce_usd, usd_try = (quotes[s] for s in GOLD_SYMBOLS)
    gram_try = ounce_usd * usd_try / TROY_OUNCE_GRAMS  # has (24 ayar) gram altın, TL
    # Çeyrek, yarım, tam, Cumhuriyet: içerdikleri saf altın kadar (işçilik hariç).
    return {a.symbol: gram_try * a.gold_grams for a in ASSETS if a.type == AssetType.GOLD}


def fetch_crypto(client: httpx.Client) -> dict[str, Decimal]:
    crypto = [a for a in ASSETS if a.type == AssetType.CRYPTO]
    try:
        response = client.get(
            COINGECKO_URL,
            params={"ids": ",".join(a.source_id for a in crypto), "vs_currencies": "try"},
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        log.warning("CoinGecko fiyatları alınamadı: %s", exc)
        return {}
    return {
        a.symbol: Decimal(str(data[a.source_id]["try"]))
        for a in crypto
        if a.source_id in data and "try" in data[a.source_id]
    }


class LiveFetcher:
    """Fiyat servisi her turda bunu çağırır (varsayılan 10 sn).

    Kripto ve altın her turda çekilir. ~630 hisse ise `stock_refresh_seconds`'ta bir (varsayılan
    60 sn) çekilir: BIST verisi Yahoo'da zaten ~16 dk gecikmeli, daha sık istemek yeni bilgi
    getirmez, sadece Yahoo'nun istek sınırına yaklaştırır. Çekilmeyen turda hisseler sonuca
    eklenmez; fiyat servisi son bilinen fiyatlarını (ve `updatedAt`'lerini) korur.
    """

    def __init__(self, stock_refresh_seconds: float, clock=time.monotonic):
        self._stock_every = stock_refresh_seconds
        self._clock = clock
        self._last_stocks: float | None = None

    def __call__(self) -> dict[str, Decimal]:
        with httpx.Client(timeout=5.0, headers=HEADERS) as client:
            prices = {**fetch_gold(client), **fetch_crypto(client)}
            now = self._clock()
            if self._last_stocks is None or now - self._last_stocks >= self._stock_every:
                stocks = fetch_stocks(client)
                if stocks:  # başarısız turda bir sonraki çağrıda yeniden denensin
                    self._last_stocks = now
                prices.update(stocks)
            return prices


fetch_live_prices = LiveFetcher(settings.stock_refresh_seconds)
