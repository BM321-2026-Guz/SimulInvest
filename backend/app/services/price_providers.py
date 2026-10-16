"""Dış fiyat kaynakları. Her fonksiyon {sembol: TL fiyatı} döner; alamadığı sembolü atlar."""

import logging
from decimal import Decimal

import httpx

from app.models import AssetType
from app.services.asset_catalog import ASSETS

log = logging.getLogger(__name__)

YAHOO_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
TROY_OUNCE_GRAMS = Decimal("31.1034768")
# Yahoo, tarayıcı olmayan istemcileri User-Agent olmadan reddediyor.
HEADERS = {"User-Agent": "Mozilla/5.0 (SimulInvest ders projesi)"}


def _yahoo_price(client: httpx.Client, yahoo_symbol: str) -> Decimal:
    response = client.get(YAHOO_URL.format(symbol=yahoo_symbol), params={"range": "1d"})
    response.raise_for_status()
    meta = response.json()["chart"]["result"][0]["meta"]
    return Decimal(str(meta["regularMarketPrice"]))


def fetch_stock_and_gold(client: httpx.Client) -> dict[str, Decimal]:
    prices: dict[str, Decimal] = {}
    for asset in ASSETS:
        if asset.type != AssetType.STOCK:
            continue
        try:
            prices[asset.symbol] = _yahoo_price(client, asset.source_id)
        except Exception as exc:  # tek bir sembolün hatası diğerlerini engellemesin
            log.warning("Yahoo fiyatı alınamadı (%s): %s", asset.symbol, exc)

    try:
        ounce_usd = _yahoo_price(client, "GC=F")
        usd_try = _yahoo_price(client, "USDTRY=X")
        prices["GRAM"] = ounce_usd * usd_try / TROY_OUNCE_GRAMS
    except Exception as exc:
        log.warning("Altın fiyatı alınamadı: %s", exc)
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
