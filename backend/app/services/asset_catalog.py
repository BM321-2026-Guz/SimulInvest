"""Desteklenen varlıklar.

`fallback_price` dış API'ye ulaşılamadığında ve hiç fiyat alınamamışken kullanılan
demo değeridir; gerçek piyasa fiyatı değildir.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.models import AssetType


@dataclass(frozen=True)
class AssetInfo:
    symbol: str
    name: str
    type: AssetType
    source_id: str  # Yahoo sembolü veya CoinGecko id'si
    fallback_price: Decimal


def _stock(symbol: str, name: str, price: str) -> AssetInfo:
    return AssetInfo(symbol, name, AssetType.STOCK, f"{symbol}.IS", Decimal(price))


def _crypto(symbol: str, name: str, coingecko_id: str, price: str) -> AssetInfo:
    return AssetInfo(symbol, name, AssetType.CRYPTO, coingecko_id, Decimal(price))


ASSETS: list[AssetInfo] = [
    _stock("THYAO", "Türk Hava Yolları", "280.00"),
    _stock("GARAN", "Garanti BBVA", "130.00"),
    _stock("AKBNK", "Akbank", "67.00"),
    _stock("ASELS", "Aselsan", "350.00"),
    _stock("BIMAS", "BİM Mağazalar", "410.00"),
    _stock("KCHOL", "Koç Holding", "210.00"),
    _stock("TUPRS", "Tüpraş", "390.00"),
    _stock("EREGL", "Ereğli Demir Çelik", "37.00"),
    _stock("SISE", "Şişecam", "37.00"),
    _stock("FROTO", "Ford Otosan", "72.00"),
    _crypto("BTC", "Bitcoin", "bitcoin", "4000000.00"),
    _crypto("ETH", "Ethereum", "ethereum", "120000.00"),
    _crypto("BNB", "BNB", "binancecoin", "36000.00"),
    _crypto("SOL", "Solana", "solana", "5100.00"),
    _crypto("XRP", "XRP", "ripple", "66.00"),
    AssetInfo("GRAM", "Gram Altın", AssetType.GOLD, "GC=F", Decimal("6500.00")),
]

ASSETS_BY_SYMBOL: dict[str, AssetInfo] = {a.symbol: a for a in ASSETS}
