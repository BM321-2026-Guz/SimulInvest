"""Desteklenen varlıklar.

- BIST hisseleri `app/data/bist_stocks.csv` dosyasından okunur (issue #56). Dosyayı
  `scripts/update_bist_list.py` Yahoo Finance'ten üretir; sıra piyasa değerine göredir.
- Kripto ve altın aşağıda elle tanımlıdır.

`fallback_price` dış kaynağa hiç ulaşılamadığında gösterilen yedek fiyattır: hisselerde liste
oluşturulurken kaydedilen son kapanış, kripto ve altında yaklaşık bir değer. API yanıtında
`isFallback: true` ile işaretlenir.
"""

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from app.models import AssetType

STOCKS_CSV = Path(__file__).resolve().parent.parent / "data" / "bist_stocks.csv"


@dataclass(frozen=True)
class AssetInfo:
    symbol: str
    name: str
    type: AssetType
    source_id: str  # Yahoo sembolü veya CoinGecko id'si
    fallback_price: Decimal


def load_stocks(path: Path = STOCKS_CSV) -> list[AssetInfo]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["rank"]))
    return [
        AssetInfo(
            r["symbol"],
            r["name"],
            AssetType.STOCK,
            f"{r['symbol']}.IS",
            Decimal(r["reference_price"]),
        )
        for r in rows
    ]


def _crypto(symbol: str, name: str, coingecko_id: str, price: str) -> AssetInfo:
    return AssetInfo(symbol, name, AssetType.CRYPTO, coingecko_id, Decimal(price))


ASSETS: list[AssetInfo] = [
    *load_stocks(),
    _crypto("BTC", "Bitcoin", "bitcoin", "4000000.00"),
    _crypto("ETH", "Ethereum", "ethereum", "120000.00"),
    _crypto("BNB", "BNB", "binancecoin", "36000.00"),
    _crypto("SOL", "Solana", "solana", "5100.00"),
    _crypto("XRP", "XRP", "ripple", "66.00"),
    AssetInfo("GRAM", "Gram Altın", AssetType.GOLD, "GC=F", Decimal("6500.00")),
]

ASSETS_BY_SYMBOL: dict[str, AssetInfo] = {a.symbol: a for a in ASSETS}
