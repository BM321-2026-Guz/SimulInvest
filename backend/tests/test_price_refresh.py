"""Fiyat hızı: 20'şerli Yahoo paketleri, hisse/kripto yenileme aralıkları, arka planda yenileme."""

import threading
import time
from decimal import Decimal

import httpx

from app.models import AssetType
from app.services import price_providers
from app.services.asset_catalog import ASSETS
from app.services.price_providers import (
    TROY_OUNCE_GRAMS,
    YAHOO_BATCH_SIZE,
    LiveFetcher,
    fetch_gold,
    fetch_stocks,
    fetch_yahoo,
)
from app.services.price_service import PriceService

STOCK_COUNT = sum(1 for a in ASSETS if a.type == AssetType.STOCK)

# ---------- Yahoo toplu istek (sahte HTTP yanıtlarıyla) ----------


def _spark_item(symbol: str, price: float) -> dict:
    return {"symbol": symbol, "response": [{"meta": {"regularMarketPrice": price}}]}


def _chart(price: float) -> dict:
    return {"chart": {"result": [{"meta": {"regularMarketPrice": price}}]}}


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def _spark_handler(calls, prices=None, fail_symbols=()):
    prices = prices or {}

    def handler(request: httpx.Request) -> httpx.Response:
        symbols = request.url.params["symbols"].split(",")
        calls.append(symbols)
        if len(symbols) > YAHOO_BATCH_SIZE:  # gerçek Yahoo davranışı
            return httpx.Response(400, json={"spark": {"result": None}})
        items = [_spark_item(s, prices.get(s, 100.0)) for s in symbols if s not in fail_symbols]
        return httpx.Response(200, json={"spark": {"result": items}})

    return handler


def test_catalog_loads_all_stocks_from_csv():
    assert STOCK_COUNT > 500  # elle yazılmış 10 hisse yerine listeden ~630
    symbols = [a.symbol for a in ASSETS if a.type == AssetType.STOCK]
    assert {"THYAO", "GARAN", "ASELS"} <= set(symbols)
    assert len(symbols) == len(set(symbols))  # tekrar yok
    thyao = next(a for a in ASSETS if a.symbol == "THYAO")
    assert thyao.name == "Türk Hava Yolları" and thyao.source_id == "THYAO.IS"


def test_stocks_are_requested_in_batches_of_20():
    calls = []
    with _client(_spark_handler(calls)) as client:
        prices = fetch_stocks(client)
    assert all(len(c) <= YAHOO_BATCH_SIZE for c in calls)
    assert len(calls) == -(-STOCK_COUNT // YAHOO_BATCH_SIZE)  # yukarı yuvarlanmış paket sayısı
    assert len(prices) == STOCK_COUNT


def test_gold_is_computed_from_ounce_and_usd_try():
    calls = []
    handler = _spark_handler(calls, prices={"GC=F": 4000.0, "USDTRY=X": 40.0})
    with _client(handler) as client:
        prices = fetch_gold(client)
    assert calls == [["GC=F", "USDTRY=X"]]
    assert prices["GRAM"] == Decimal("4000.0") * Decimal("40.0") / TROY_OUNCE_GRAMS


def test_few_missing_symbols_fall_back_to_single_requests():
    calls = []
    spark = _spark_handler(calls, fail_symbols={"GARAN.IS"})

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/spark"):
            return spark(request)
        return httpx.Response(200, json=_chart(50.0))

    with _client(handler) as client:
        prices = fetch_yahoo(client, ["THYAO.IS", "GARAN.IS"])
    assert prices == {"THYAO.IS": Decimal("100.0"), "GARAN.IS": Decimal("50.0")}


def test_many_missing_symbols_are_not_retried_one_by_one():
    single_calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/spark"):
            return httpx.Response(500)
        single_calls.append(request.url.path)
        return httpx.Response(200, json=_chart(1.0))

    with _client(handler) as client:
        prices = fetch_yahoo(client, [f"S{i}.IS" for i in range(60)])
    assert prices == {} and single_calls == []  # 60 tek istek atılmadı


def test_yahoo_completely_down_returns_nothing():
    with _client(lambda request: httpx.Response(503)) as client:
        assert fetch_stocks(client) == {}
        assert fetch_gold(client) == {}


def test_live_fetcher_refreshes_stocks_less_often(monkeypatch):
    now = [0.0]
    stock_calls = []
    monkeypatch.setattr(price_providers, "fetch_gold", lambda c: {"GRAM": Decimal(1)})
    monkeypatch.setattr(price_providers, "fetch_crypto", lambda c: {"BTC": Decimal(2)})
    monkeypatch.setattr(
        price_providers,
        "fetch_stocks",
        lambda c: stock_calls.append(now[0]) or {"THYAO": Decimal(3)},
    )
    fetcher = LiveFetcher(stock_refresh_seconds=60, clock=lambda: now[0])

    assert "THYAO" in fetcher()  # ilk turda hisseler de gelir
    now[0] = 10
    second = fetcher()
    assert "THYAO" not in second and "BTC" in second  # 10 sn sonra sadece kripto/altın
    now[0] = 61
    assert "THYAO" in fetcher()
    assert stock_calls == [0.0, 61]


def test_live_fetcher_retries_stocks_after_a_failed_round(monkeypatch):
    now = [0.0]
    results = [{}, {"THYAO": Decimal(3)}]
    monkeypatch.setattr(price_providers, "fetch_gold", lambda c: {})
    monkeypatch.setattr(price_providers, "fetch_crypto", lambda c: {})
    monkeypatch.setattr(price_providers, "fetch_stocks", lambda c: results.pop(0))
    fetcher = LiveFetcher(stock_refresh_seconds=60, clock=lambda: now[0])
    assert fetcher() == {}
    now[0] = 10  # başarısız turdan sonra 60 sn beklenmez
    assert fetcher() == {"THYAO": Decimal(3)}


# ---------- arka planda yenileme ----------


def test_background_refresh_updates_prices_over_time():
    counter = {"n": 0}
    fetched = threading.Event()

    def rising():
        counter["n"] += 1
        if counter["n"] >= 3:
            fetched.set()
        return {"THYAO": Decimal(100 + counter["n"])}

    service = PriceService(rising, cache_seconds=60)
    service.start(interval=0.01)
    try:
        assert fetched.wait(5)
        assert service.get("THYAO").price > Decimal("102")
    finally:
        service.stop()
    assert not service.is_running


def test_requests_do_not_wait_for_slow_source_when_running():
    first_done = threading.Event()

    def slow():
        if first_done.is_set():
            time.sleep(1)  # sonraki yenilemeler yavaş
        first_done.set()
        return {"THYAO": Decimal("280")}

    service = PriceService(slow, cache_seconds=0)
    service.start(interval=0)
    try:
        assert first_done.wait(5)
        time.sleep(0.05)  # arka plan şu an yavaş yenilemenin içinde
        start = time.monotonic()
        quote = service.get("THYAO")
        assert time.monotonic() - start < 0.2
        assert quote.price == Decimal("280")
    finally:
        service.stop()


def test_start_is_idempotent_and_stop_without_start_is_safe():
    service = PriceService(dict, cache_seconds=60)
    service.stop()  # başlatılmadan durdurmak hata vermez
    service.start(interval=0.01)
    thread = service._thread
    service.start(interval=0.01)  # ikinci start yeni thread açmaz
    assert service._thread is thread
    service.stop()


def test_gold_coins_are_priced_by_their_pure_gold():
    calls = []
    handler = _spark_handler(calls, prices={"GC=F": 4000.0, "USDTRY=X": 40.0})
    with _client(handler) as client:
        prices = fetch_gold(client)
    gram = Decimal("4000.0") * Decimal("40.0") / TROY_OUNCE_GRAMS
    assert set(prices) == {"GRAM", "CEYREK", "YARIM", "TAM", "CUMHURIYET"}
    # Çeyrek: 1,75 g × 22/24 = 1,6042 g saf altın
    assert prices["CEYREK"] == gram * Decimal("1.6042")
    assert prices["YARIM"] == gram * Decimal("3.2083")
    assert prices["CUMHURIYET"] > prices["TAM"] > prices["YARIM"] > prices["CEYREK"] > gram
