"""Fiyat hızı: Yahoo toplu istek ve arka planda yenileme."""

import threading
import time
from decimal import Decimal

import httpx

from app.services.price_providers import TROY_OUNCE_GRAMS, fetch_stock_and_gold
from app.services.price_service import PriceService

# ---------- Yahoo toplu istek (sahte HTTP yanıtlarıyla) ----------


def _spark_item(symbol: str, price: float) -> dict:
    return {"symbol": symbol, "response": [{"meta": {"regularMarketPrice": price}}]}


def _chart(price: float) -> dict:
    return {"chart": {"result": [{"meta": {"regularMarketPrice": price}}]}}


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_batch_request_fetches_all_symbols_in_one_call():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.url.path)
        symbols = request.url.params["symbols"].split(",")
        prices = {"GC=F": 4000.0, "USDTRY=X": 40.0}
        return httpx.Response(
            200,
            json={"spark": {"result": [_spark_item(s, prices.get(s, 100.0)) for s in symbols]}},
        )

    with _client(handler) as client:
        prices = fetch_stock_and_gold(client)

    assert calls == ["/v7/finance/spark"]  # 12 sembol tek istekte
    assert prices["THYAO"] == Decimal("100.0")
    assert len([s for s in prices if s != "GRAM"]) == 10
    assert prices["GRAM"] == Decimal("4000.0") * Decimal("40.0") / TROY_OUNCE_GRAMS


def test_missing_symbols_fall_back_to_single_requests():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/spark"):
            # Toplu yanıtta sadece THYAO var; diğerleri tek tek istenmeli.
            return httpx.Response(200, json={"spark": {"result": [_spark_item("THYAO.IS", 300)]}})
        return httpx.Response(200, json=_chart(50.0))

    with _client(handler) as client:
        prices = fetch_stock_and_gold(client)

    assert prices["THYAO"] == Decimal("300")
    assert prices["GARAN"] == Decimal("50.0")
    assert "GRAM" in prices


def test_batch_failure_falls_back_to_single_requests():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/spark"):
            return httpx.Response(500)
        return httpx.Response(200, json=_chart(75.0))

    with _client(handler) as client:
        prices = fetch_stock_and_gold(client)

    assert prices["AKBNK"] == Decimal("75.0")


def test_yahoo_completely_down_returns_nothing():
    with _client(lambda request: httpx.Response(503)) as client:
        assert fetch_stock_and_gold(client) == {}


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
