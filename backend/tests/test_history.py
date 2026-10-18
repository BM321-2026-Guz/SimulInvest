"""Issue #49: varlık fiyat geçmişi ve günlük özet (sahte Yahoo verisiyle, internet gerekmez)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from app.main import app
from app.services.history_service import (
    TROY_OUNCE_GRAMS,
    HistoryService,
    Series,
    get_history_service,
)

DAYS = [datetime(2026, 10, d, 7, 0, tzinfo=UTC) for d in (13, 14, 15, 16)]


class FakeYahoo:
    """(sembol, range, interval) → Series; çağrıları sayar."""

    def __init__(self):
        self.calls = []
        self.fail = False

    def __call__(self, symbol, range_, interval):
        self.calls.append((symbol, range_, interval))
        if self.fail:
            raise RuntimeError("Yahoo kapalı")
        if symbol == "USDTRY=X":
            return Series(times=DAYS, closes=[40.0, 40.0, 41.0, 42.0])
        if interval == "60m":
            hours = [datetime(2026, 10, 16, h, tzinfo=UTC) for h in (7, 8, 9)]
            return Series(times=hours, closes=[100.0, None, 102.0])
        return Series(
            times=DAYS,
            opens=[90.0, 95.0, 98.0, 99.0],
            closes=[94.0, 97.0, 98.5, 101.0],
            day_high=103.0,
            day_low=97.5,
        )


@pytest.fixture
def yahoo():
    return FakeYahoo()


@pytest.fixture
def history_client(client, yahoo):
    service = HistoryService(yahoo, cache_seconds=60)
    app.dependency_overrides[get_history_service] = lambda: service
    return client


def test_stock_history_and_day_summary(history_client, yahoo):
    body = history_client.get("/api/assets/THYAO/history").json()
    assert yahoo.calls == [("THYAO.IS", "1mo", "1d")]  # günlük aralıkta tek istek yeter
    assert body["symbol"] == "THYAO" and body["range"] == "1mo"
    assert [p["price"] for p in body["points"]] == [94.0, 97.0, 98.5, 101.0]
    assert body["open"] == 99.0  # son günün açılışı
    assert body["previousClose"] == 98.5  # bir önceki günün kapanışı (chartPreviousClose değil)
    assert body["dayLow"] == 97.5 and body["dayHigh"] == 103.0


def test_five_day_range_uses_hourly_points_and_daily_summary(history_client, yahoo):
    body = history_client.get("/api/assets/THYAO/history", params={"range": "5d"}).json()
    assert ("THYAO.IS", "5d", "60m") in yahoo.calls and ("THYAO.IS", "5d", "1d") in yahoo.calls
    assert [p["price"] for p in body["points"]] == [100.0, 102.0]  # boş nokta atlanır
    assert body["open"] == 99.0


def test_crypto_is_converted_with_that_days_usd_try_rate(history_client, yahoo):
    body = history_client.get("/api/assets/BTC/history").json()
    assert ("BTC-USD", "1mo", "1d") in yahoo.calls
    assert [p["price"] for p in body["points"]] == [94 * 40, 97 * 40, 98.5 * 41, 101 * 42]
    assert body["previousClose"] == 98.5 * 41
    assert body["dayHigh"] == 103 * 42


def test_gold_is_converted_to_grams(history_client):
    body = history_client.get("/api/assets/GRAM/history").json()
    expected = (Decimal("101") * 42 / TROY_OUNCE_GRAMS).quantize(Decimal("0.00000001"))
    assert body["points"][-1]["price"] == float(expected)


def test_results_are_cached(history_client, yahoo):
    history_client.get("/api/assets/THYAO/history")
    history_client.get("/api/assets/thyao/history")
    assert len(yahoo.calls) == 1


def test_unknown_symbol_returns_404(history_client):
    response = history_client.get("/api/assets/YOKBOYLE/history")
    assert response.status_code == 404
    assert response.json()["code"] == "ASSET_NOT_FOUND"


def test_invalid_range_is_rejected(history_client):
    response = history_client.get("/api/assets/THYAO/history", params={"range": "10y"})
    assert response.status_code == 400


def test_missing_opens_do_not_break_summary(history_client):
    service = HistoryService(
        lambda *a: Series(times=DAYS, opens=[], closes=[1.0, 2.0, 3.0, 4.0]), cache_seconds=0
    )
    app.dependency_overrides[get_history_service] = lambda: service
    body = history_client.get("/api/assets/THYAO/history").json()
    assert body["open"] is None and body["previousClose"] == 3.0


def test_source_down_returns_503_not_500(history_client, yahoo):
    yahoo.fail = True
    response = history_client.get("/api/assets/THYAO/history")
    assert response.status_code == 503
    assert response.json()["code"] == "HISTORY_UNAVAILABLE"


def test_empty_series_returns_503(history_client):
    service = HistoryService(lambda *a: Series(times=[]), cache_seconds=0)
    app.dependency_overrides[get_history_service] = lambda: service
    assert history_client.get("/api/assets/THYAO/history").status_code == 503
