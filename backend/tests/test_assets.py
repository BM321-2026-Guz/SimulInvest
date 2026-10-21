from decimal import Decimal

from app.services.asset_catalog import ASSETS_BY_SYMBOL
from app.services.price_service import PriceService


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_list_assets_includes_all_types(client):
    assets = client.get("/api/assets").json()
    assert {a["type"] for a in assets} == {"STOCK", "CRYPTO", "GOLD"}
    thyao = next(a for a in assets if a["symbol"] == "THYAO")
    assert thyao["price"] == 300.0
    assert thyao["name"] == "Türk Hava Yolları"


def test_fallback_flag_marks_demo_prices(client):
    # Sahte kaynak sadece THYAO ve BTC fiyatı veriyor; diğerleri katalogdaki demo fiyatta.
    assets = {a["symbol"]: a for a in client.get("/api/assets").json()}
    assert assets["THYAO"]["isFallback"] is False
    assert assets["BTC"]["isFallback"] is False
    assert assets["GARAN"]["isFallback"] is True
    assert client.get("/api/assets/GARAN").json()["isFallback"] is True


def test_last_known_price_is_not_marked_as_fallback():
    state = {"fail": False}

    def flaky():
        if state["fail"]:
            raise RuntimeError("API kapalı")
        return {"GARAN": Decimal("142.10")}

    service = PriceService(flaky, cache_seconds=0)
    assert service.get("GARAN").is_fallback is False
    state["fail"] = True
    # Gerçek ama eski fiyat: demo değil, yaşı updatedAt alanından anlaşılır.
    assert service.get("GARAN").is_fallback is False


def test_filter_assets_by_type(client):
    assets = client.get("/api/assets", params={"type": "CRYPTO"}).json()
    assert assets and all(a["type"] == "CRYPTO" for a in assets)


def test_get_single_asset_is_case_insensitive(client):
    assert client.get("/api/assets/thyao").json()["symbol"] == "THYAO"


def test_unknown_asset_returns_404(client):
    response = client.get("/api/assets/YOKBOYLE")
    assert response.status_code == 404
    assert response.json()["code"] == "ASSET_NOT_FOUND"


def test_fallback_price_when_source_fails():
    def broken():
        raise RuntimeError("API kapalı")

    service = PriceService(broken, cache_seconds=0)
    assert service.get("GARAN").price == ASSETS_BY_SYMBOL["GARAN"].fallback_price


def test_last_known_price_is_kept_when_source_fails():
    state = {"fail": False}

    def flaky():
        if state["fail"]:
            raise RuntimeError("API kapalı")
        return {"GARAN": Decimal("142.10")}

    service = PriceService(flaky, cache_seconds=0)
    assert service.get("GARAN").price == Decimal("142.10")
    state["fail"] = True
    assert service.get("GARAN").price == Decimal("142.10")


def test_prices_are_cached():
    calls = []

    def counting():
        calls.append(1)
        return {}

    service = PriceService(counting, cache_seconds=60)
    service.get_all()
    service.get("THYAO")
    assert len(calls) == 1


def test_market_has_30_coins_and_5_gold_types(client):
    assets = client.get("/api/assets").json()
    by_type = {}
    for a in assets:
        by_type.setdefault(a["type"], []).append(a["symbol"])
    assert len(by_type["CRYPTO"]) == 30
    assert by_type["GOLD"] == ["GRAM", "CEYREK", "YARIM", "TAM", "CUMHURIYET"]


def test_whole_units_flag(client):
    assets = {a["symbol"]: a for a in client.get("/api/assets").json()}
    assert assets["THYAO"]["wholeUnits"] is True
    assert assets["CEYREK"]["wholeUnits"] is True
    assert assets["GRAM"]["wholeUnits"] is False
    assert assets["BTC"]["wholeUnits"] is False
