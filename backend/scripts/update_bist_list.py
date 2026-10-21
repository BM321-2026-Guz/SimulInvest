"""BIST hisse listesini Yahoo Finance'ten oluşturur (issue #56).

Çıktı: backend/app/data/bist_stocks.csv (rank, symbol, name, reference_price, last_trade)
`rank`: piyasa değerine göre sıra (1 = en büyük); arayüz büyük şirketleri önce gösterir.

Uygulama her açılışta dış siteye bağımlı olmasın diye liste repoda dosya olarak tutulur; bu
betik ayda bir (ya da yeni halka arzlarda) elle çalıştırılır ve değişiklik PR ile gönderilir:

    cd backend
    .venv/Scripts/python.exe scripts/update_bist_list.py

Adımlar:
1. Yahoo screener'dan Borsa İstanbul'daki (exchange=IST) bütün hisseleri al.
2. Her hissenin fiyatını Yahoo'dan 20'şerli paketlerle doğrula; fiyatı gelmeyen veya son
   MAX_STALE_DAYS günde işlem görmemiş ya da fiyatı başlangıç bakiyesini (MAX_PRICE_TL) aşanları
   listeye alma.
3. Adları sadeleştir ("A.S.", "Anonim Sirketi" vb. at); bilinen hisselerde Türkçe adı kullan.
"""

import argparse
import csv
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import httpx

OUT = Path(__file__).resolve().parent.parent / "app" / "data" / "bist_stocks.csv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/130.0 Safari/537.36"
}
SCREENER_URL = "https://query2.finance.yahoo.com/v1/finance/screener"
SPARK_URL = "https://query1.finance.yahoo.com/v7/finance/spark"
BATCH = 20  # Yahoo tek istekte en fazla 20 sembol kabul ediyor
MAX_STALE_DAYS = 30
# Başlangıç bakiyesiyle bir adet bile alınamayan hisseler (ör. ISBTR ~396.000 TL) listeye alınmaz.
MAX_PRICE_TL = 100_000

# Yahoo adları Türkçe karaktersiz ve uzun geliyor; bilinen hisselerde düzgün ad kullanılır.
NAME_OVERRIDES = {
    "THYAO": "Türk Hava Yolları",
    "GARAN": "Garanti BBVA",
    "AKBNK": "Akbank",
    "ASELS": "Aselsan",
    "BIMAS": "BİM Mağazalar",
    "KCHOL": "Koç Holding",
    "TUPRS": "Tüpraş",
    "EREGL": "Ereğli Demir Çelik",
    "SISE": "Şişecam",
    "FROTO": "Ford Otosan",
    "ISCTR": "İş Bankası (C)",
    "YKBNK": "Yapı Kredi",
    "SAHOL": "Sabancı Holding",
    "TCELL": "Turkcell",
    "TTKOM": "Türk Telekom",
    "PGSUS": "Pegasus",
    "TOASO": "Tofaş",
    "ARCLK": "Arçelik",
    "ENKAI": "Enka İnşaat",
    "HALKB": "Halkbank",
    "VAKBN": "VakıfBank",
}

LEGAL_SUFFIX = re.compile(
    r"[\s,]+(T\.?\s?A\.?\s?[SŞ]\.?|A\.?\s?[SŞ]\.?|Anonim\s+[SŞ]irketi|Türk\s+Anonim\s+[SŞ]irketi)\s*$",
    re.IGNORECASE,
)


def clean_name(symbol: str, raw: str | None) -> str:
    if symbol in NAME_OVERRIDES:
        return NAME_OVERRIDES[symbol]
    name = (raw or symbol).strip()
    for _ in range(2):  # "... Ticaret Anonim Sirketi A.S." gibi çift ekler
        name = LEGAL_SUFFIX.sub("", name).strip()
    return name or symbol


def screener_symbols(client: httpx.Client) -> list[tuple[str, str | None]]:
    """(sembol, ad) listesi, piyasa değerine göre büyükten küçüğe."""
    client.get("https://fc.yahoo.com")  # crumb için çerez
    crumb = client.get("https://query2.finance.yahoo.com/v1/test/getcrumb").text.strip()
    body = {
        "size": 250,
        "offset": 0,
        "sortField": "intradaymarketcap",
        "sortType": "DESC",
        "quoteType": "EQUITY",
        "userId": "",
        "userIdType": "guid",
        "query": {
            "operator": "AND",
            "operands": [{"operator": "eq", "operands": ["exchange", "IST"]}],
        },
    }
    found: dict[str, str | None] = {}
    while True:
        r = client.post(SCREENER_URL, params={"crumb": crumb}, json=body)
        r.raise_for_status()
        result = r.json()["finance"]["result"][0]
        quotes = result.get("quotes") or []
        for q in quotes:
            if q.get("symbol", "").endswith(".IS"):
                found[q["symbol"]] = q.get("longName") or q.get("shortName")
        body["offset"] += len(quotes)
        if not quotes or body["offset"] >= result.get("total", 0):
            return list(found.items())


def spark(client: httpx.Client, symbols: list[str]) -> dict[str, dict]:
    for attempt in range(3):
        r = client.get(
            SPARK_URL, params={"symbols": ",".join(symbols), "range": "1d", "interval": "1d"}
        )
        if r.status_code == 200:
            items = (r.json().get("spark") or {}).get("result") or []
            return {i["symbol"]: i["response"][0]["meta"] for i in items if i.get("response")}
        time.sleep(2 * (attempt + 1))
    return {}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=OUT)
    args = parser.parse_args()

    with httpx.Client(headers=HEADERS, timeout=15, follow_redirects=True) as client:
        candidates = screener_symbols(client)
        print(f"Yahoo screener: {len(candidates)} hisse (exchange=IST)")
        names = dict(candidates)
        chunks = [list(names)[i : i + BATCH] for i in range(0, len(names), BATCH)]
        metas: dict[str, dict] = {}
        with ThreadPoolExecutor(max_workers=4) as pool:
            for part in pool.map(lambda c: spark(client, c), chunks):
                metas.update(part)

    now = time.time()
    rows, skipped = [], []
    for rank, ysym in enumerate(names, start=1):
        meta = metas.get(ysym) or {}
        price, traded = meta.get("regularMarketPrice"), meta.get("regularMarketTime")
        symbol = ysym.removesuffix(".IS")
        if not price or price <= 0 or not traded:
            skipped.append((symbol, "fiyat yok"))
        elif price > MAX_PRICE_TL:
            skipped.append((symbol, f"fiyat {price:,.0f} TL, başlangıç bakiyesinden yüksek"))
        elif now - traded > MAX_STALE_DAYS * 86400:
            skipped.append((symbol, f"{int((now - traded) / 86400)} gündür işlem yok"))
        else:
            rows.append(
                {
                    "rank": rank,
                    "symbol": symbol,
                    "name": clean_name(symbol, names[ysym]),
                    "reference_price": f"{price:.4f}".rstrip("0").rstrip("."),
                    "last_trade": datetime.fromtimestamp(traded, UTC).date().isoformat(),
                }
            )

    for i, row in enumerate(rows, start=1):  # alınmayanlar çıkınca sıra boşluksuz olsun
        row["rank"] = i
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["rank", "symbol", "name", "reference_price", "last_trade"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Yazıldı: {args.out} ({len(rows)} hisse)")
    print(f"Alınmayan: {len(skipped)}")
    for symbol, why in skipped:
        print(f"  {symbol:8} {why}")
    return 0 if rows else 1


if __name__ == "__main__":
    sys.exit(main())
