"""Dış fiyat kaynakları. Her fonksiyon {sembol: TL fiyatı} döner; alamadığı sembolü atlar."""

import logging
from decimal import Decimal

import httpx

from app.models import AssetType
from app.services.asset_catalog import ASSETS

log = logging.getLogger(__name__)

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
# Tek istekte birden çok sembol: 12 sembol için ~0,5 sn (tek tek ~2,6 sn).
YAHOO_BATCH_URL = "https://query1.finance.yahoo.com/v7/finance/spark"
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
    """Toplu istek; hata olursa boş döner, eksik semboller tek tek denenir."""
    try:
        response = client.get(
            YAHOO_BATCH_URL,
            params={"symbols": ",".join(yahoo_symbols), "range": "1d", "interval": "1d"},
        )
        response.raise_for_status()
        results = response.json()["spark"]["result"] or []
    except Exception as exc:
        log.warning("Yahoo toplu fiyat isteği başarısız, tek tek denenecek: %s", exc)
        return {}
    prices = {}
    for item in results:
        try:
            meta = item["response"][0]["meta"]
            prices[item["symbol"]] = Decimal(str(meta["regularMarketPrice"]))
        except (KeyError, IndexError, TypeError):
            continue
    return prices


def fetch_stock_and_gold(client: httpx.Client) -> dict[str, Decimal]:
    stocks = {a.source_id: a.symbol for a in ASSETS if a.type == AssetType.STOCK}
    wanted = [*stocks, *GOLD_SYMBOLS]
    quotes = _yahoo_batch(client, wanted)

    for yahoo_symbol in wanted:
        if yahoo_symbol in quotes:
            continue
        try:
            quotes[yahoo_symbol] = _yahoo_price(client, yahoo_symbol)
        except Exception as exc:  # tek bir sembolün hatası diğerlerini engellemesin
            log.warning("Yahoo fiyatı alınamadı (%s): %s", yahoo_symbol, exc)

    prices = {symbol: quotes[ysym] for ysym, symbol in stocks.items() if ysym in quotes}
    if all(s in quotes for s in GOLD_SYMBOLS):
        ounce_usd, usd_try = (quotes[s] for s in GOLD_SYMBOLS)
        prices["GRAM"] = ounce_usd * usd_try / TROY_OUNCE_GRAMS
    return prices


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


def fetch_live_prices() -> dict[str, Decimal]:
    with httpx.Client(timeout=5.0, headers=HEADERS) as client:
        return {**fetch_stock_and_gold(client), **fetch_crypto(client)}
