"""Desteklenen varlıklar.

- BIST hisseleri `app/data/bist_stocks.csv` dosyasından okunur (issue #56). Dosyayı
  `scripts/update_bist_list.py` Yahoo Finance'ten üretir; sıra piyasa değerine göredir.
- Kripto (piyasa değerine göre ilk 30) ve altın türleri aşağıda tanımlıdır (issue #57).

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
    source_id: str  # canlı fiyat kaynağındaki kimlik: Yahoo sembolü veya CoinGecko id'si
    fallback_price: Decimal
    chart_symbol: str = ""  # fiyat geçmişi (grafik) için Yahoo sembolü
    whole_units: bool = False  # True: sadece tam adet alınıp satılır (hisse, sikke altın)
    gold_grams: Decimal | None = None  # altında içerdiği saf (24 ayar) altın, gram


def load_stocks(path: Path = STOCKS_CSV) -> list[AssetInfo]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = sorted(csv.DictReader(f), key=lambda r: int(r["rank"]))
    return [
        AssetInfo(
            symbol=r["symbol"],
            name=r["name"],
            type=AssetType.STOCK,
            source_id=f"{r['symbol']}.IS",
            fallback_price=Decimal(r["reference_price"]),
            chart_symbol=f"{r['symbol']}.IS",
            whole_units=True,
        )
        for r in rows
    ]


# (sembol, ad, CoinGecko id, Yahoo grafik sembolü, yaklaşık TL fiyatı) — piyasa değerine göre.
# Yahoo'da bazı coinlerin sembolü sayı ekiyle tutuluyor (ör. SUI20947-USD); hepsi 21 Ekim'de
# CoinGecko (TL fiyat) ve Yahoo (USD geçmiş) üzerinde doğrulandı.
_CRYPTO = [
    ("BTC", "Bitcoin", "bitcoin", "BTC-USD", "4180000"),
    ("ETH", "Ethereum", "ethereum", "ETH-USD", "123000"),
    ("USDT", "Tether", "tether", "USDT-USD", "49.5"),
    ("XRP", "XRP", "ripple", "XRP-USD", "68"),
    ("BNB", "BNB", "binancecoin", "BNB-USD", "37000"),
    ("SOL", "Solana", "solana", "SOL-USD", "5330"),
    ("USDC", "USD Coin", "usd-coin", "USDC-USD", "49.5"),
    ("DOGE", "Dogecoin", "dogecoin", "DOGE-USD", "4.1"),
    ("TRX", "TRON", "tron", "TRX-USD", "16.4"),
    ("ADA", "Cardano", "cardano", "ADA-USD", "11.2"),
    # Chainlink (LINK) yok: BIST'teki LINK (Link Bilgisayar) ile aynı sembol olurdu.
    ("AAVE", "Aave", "aave", "AAVE-USD", "7770"),
    ("AVAX", "Avalanche", "avalanche-2", "AVAX-USD", "484"),
    ("XLM", "Stellar", "stellar", "XLM-USD", "9.2"),
    ("SUI", "Sui", "sui", "SUI20947-USD", "51.5"),
    ("BCH", "Bitcoin Cash", "bitcoin-cash", "BCH-USD", "14270"),
    ("HBAR", "Hedera", "hedera-hashgraph", "HBAR-USD", "4.2"),
    ("LTC", "Litecoin", "litecoin", "LTC-USD", "3050"),
    ("TON", "Toncoin", "the-open-network", "TON11419-USD", "67"),
    ("SHIB", "Shiba Inu", "shiba-inu", "SHIB-USD", "0.00026"),
    ("DOT", "Polkadot", "polkadot", "DOT-USD", "58"),
    ("UNI", "Uniswap", "uniswap", "UNI7083-USD", "372"),
    ("PEPE", "Pepe", "pepe", "PEPE24478-USD", "0.00023"),
    ("NEAR", "NEAR Protocol", "near", "NEAR-USD", "260"),
    ("APT", "Aptos", "aptos", "APT21794-USD", "41"),
    ("ICP", "Internet Computer", "internet-computer", "ICP-USD", "146"),
    ("ETC", "Ethereum Classic", "ethereum-classic", "ETC-USD", "402"),
    ("ATOM", "Cosmos", "cosmos", "ATOM-USD", "87"),
    ("FIL", "Filecoin", "filecoin", "FIL-USD", "52"),
    ("ARB", "Arbitrum", "arbitrum", "ARB11841-USD", "9.6"),
    ("RENDER", "Render", "render-token", "RENDER-USD", "94"),
]

# Altın: gram altın 24 ayar; sikkeler 22 ayar (saf altın = ağırlık × 22/24).
# Fiyat = has gram altın fiyatı × içerdiği saf altın; kuyumcu işçiliği dahil değildir.
GRAM_FALLBACK = Decimal("6500")
_TWENTY_TWO_K = Decimal(22) / Decimal(24)
_GOLD = [
    # (sembol, ad, ağırlık (g), ayar oranı, tam adet mi)
    ("GRAM", "Gram Altın (24 ayar)", Decimal("1"), Decimal(1), False),
    ("CEYREK", "Çeyrek Altın", Decimal("1.75"), _TWENTY_TWO_K, True),
    ("YARIM", "Yarım Altın", Decimal("3.50"), _TWENTY_TWO_K, True),
    ("TAM", "Tam Altın", Decimal("7.00"), _TWENTY_TWO_K, True),
    ("CUMHURIYET", "Cumhuriyet Altını", Decimal("7.216"), _TWENTY_TWO_K, True),
]


def _gold(symbol: str, name: str, weight: Decimal, purity: Decimal, whole: bool) -> AssetInfo:
    grams = (weight * purity).quantize(Decimal("0.0001"))
    return AssetInfo(
        symbol=symbol,
        name=name,
        type=AssetType.GOLD,
        source_id="GC=F",
        fallback_price=(GRAM_FALLBACK * grams).quantize(Decimal("0.01")),
        chart_symbol="GC=F",
        whole_units=whole,
        gold_grams=grams,
    )


ASSETS: list[AssetInfo] = [
    *load_stocks(),
    *(
        AssetInfo(sym, name, AssetType.CRYPTO, cg_id, Decimal(price), chart_symbol=ysym)
        for sym, name, cg_id, ysym, price in _CRYPTO
    ),
    *(_gold(*g) for g in _GOLD),
]

ASSETS_BY_SYMBOL: dict[str, AssetInfo] = {a.symbol: a for a in ASSETS}

# Portföy ve işlem geçmişi varlıkları sembolle tutar; aynı sembol iki varlıkta olamaz. BIST listesi
# güncellenince yeni bir hisse bir coinle çakışırsa uygulama açılmaz, hangi sembol olduğu yazılır.
_duplicates = sorted({a.symbol for a in ASSETS if sum(b.symbol == a.symbol for b in ASSETS) > 1})
if _duplicates:
    raise RuntimeError(f"Aynı sembol birden fazla varlıkta: {', '.join(_duplicates)}")
