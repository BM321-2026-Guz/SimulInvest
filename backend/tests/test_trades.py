from decimal import Decimal


def trade(client, headers, symbol, side, quantity):
    return client.post(
        "/api/trades",
        headers=headers,
        json={"symbol": symbol, "side": side, "quantity": quantity},
    )


def portfolio(client, headers):
    return client.get("/api/portfolio", headers=headers).json()


def test_buy_reduces_balance_and_adds_holding(client, auth_headers):
    response = trade(client, auth_headers, "THYAO", "BUY", 10)
    assert response.status_code == 201
    tx = response.json()
    assert tx["side"] == "BUY"
    assert tx["price"] == 300.0
    assert tx["total"] == 3000.0
    assert isinstance(tx["id"], str)

    p = portfolio(client, auth_headers)
    assert p["balance"] == 97000.0
    assert p["holdings"][0]["symbol"] == "THYAO"
    assert p["holdings"][0]["quantity"] == 10.0
    assert p["totalValue"] == 100000.0


def test_buy_with_insufficient_balance_is_rejected(client, auth_headers):
    # Senaryo 1: 1 BTC = 2.000.000 TL > 100.000 TL
    response = trade(client, auth_headers, "BTC", "BUY", 1)
    assert response.status_code == 400
    assert response.json()["code"] == "INSUFFICIENT_BALANCE"
    assert portfolio(client, auth_headers)["balance"] == 100000.0


def test_buy_exact_balance_leaves_zero(client, auth_headers, fake_prices):
    fake_prices.prices["THYAO"] = Decimal("1000")
    assert trade(client, auth_headers, "THYAO", "BUY", 100).status_code == 201
    assert portfolio(client, auth_headers)["balance"] == 0.0
    assert trade(client, auth_headers, "THYAO", "BUY", 1).status_code == 400


def test_sell_unowned_asset_is_rejected(client, auth_headers):
    # Senaryo 2
    response = trade(client, auth_headers, "THYAO", "SELL", 1)
    assert response.status_code == 400
    assert response.json()["code"] == "INSUFFICIENT_QUANTITY"


def test_sell_more_than_owned_is_rejected(client, auth_headers):
    trade(client, auth_headers, "THYAO", "BUY", 5)
    response = trade(client, auth_headers, "THYAO", "SELL", 6)
    assert response.status_code == 400
    assert portfolio(client, auth_headers)["holdings"][0]["quantity"] == 5.0


def test_sell_updates_balance_and_holding(client, auth_headers, fake_prices):
    # Senaryo 6
    trade(client, auth_headers, "THYAO", "BUY", 10)
    fake_prices.prices["THYAO"] = Decimal("350")
    assert trade(client, auth_headers, "THYAO", "SELL", 4).status_code == 201

    p = portfolio(client, auth_headers)
    assert p["balance"] == 97000.0 + 1400.0
    h = p["holdings"][0]
    assert h["quantity"] == 6.0
    assert h["averageCost"] == 300.0  # satışta maliyet değişmez
    assert h["profitLoss"] == 300.0  # (350 - 300) * 6


def test_selling_everything_removes_holding(client, auth_headers):
    trade(client, auth_headers, "THYAO", "BUY", 3)
    trade(client, auth_headers, "THYAO", "SELL", 3)
    assert portfolio(client, auth_headers)["holdings"] == []


def test_average_cost_is_weighted(client, auth_headers, fake_prices):
    trade(client, auth_headers, "THYAO", "BUY", 10)  # 10 x 300
    fake_prices.prices["THYAO"] = Decimal("400")
    trade(client, auth_headers, "THYAO", "BUY", 30)  # 30 x 400
    h = portfolio(client, auth_headers)["holdings"][0]
    assert h["quantity"] == 40.0
    assert h["averageCost"] == 375.0  # (3000 + 12000) / 40


def test_negative_or_zero_quantity_is_rejected(client, auth_headers):
    # Senaryo 7
    for qty in (-5, 0):
        response = trade(client, auth_headers, "THYAO", "BUY", qty)
        assert response.status_code == 400
        assert response.json()["code"] == "VALIDATION_ERROR"
    assert client.get("/api/transactions", headers=auth_headers).json() == []


def test_fractional_stock_quantity_is_rejected(client, auth_headers):
    response = trade(client, auth_headers, "THYAO", "BUY", 1.5)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_QUANTITY"


def test_fractional_crypto_quantity_is_allowed(client, auth_headers):
    response = trade(client, auth_headers, "BTC", "BUY", 0.01)
    assert response.status_code == 201
    assert response.json()["total"] == 20000.0


def test_unknown_symbol_returns_404(client, auth_headers):
    assert trade(client, auth_headers, "YOKBOYLE", "BUY", 1).status_code == 404


def test_trade_requires_auth(client):
    response = client.post("/api/trades", json={"symbol": "THYAO", "side": "BUY", "quantity": 1})
    assert response.status_code == 401


def test_transactions_are_listed_newest_first(client, auth_headers):
    trade(client, auth_headers, "THYAO", "BUY", 2)
    trade(client, auth_headers, "THYAO", "SELL", 1)
    txs = client.get("/api/transactions", headers=auth_headers).json()
    assert [t["side"] for t in txs] == ["SELL", "BUY"]


def test_users_cannot_see_each_others_data(client, auth_headers):
    trade(client, auth_headers, "THYAO", "BUY", 1)
    other = client.post(
        "/api/auth/register", json={"email": "mehmet@example.com", "password": "12345678"}
    ).json()["token"]
    headers = {"Authorization": f"Bearer {other}"}
    assert client.get("/api/transactions", headers=headers).json() == []
    assert portfolio(client, headers)["holdings"] == []


def test_created_at_is_utc(client, auth_headers):
    created = trade(client, auth_headers, "THYAO", "BUY", 1).json()["createdAt"]
    assert created.endswith(("Z", "+00:00"))


def test_gold_coins_trade_in_whole_units_only(client, auth_headers):
    response = trade(client, auth_headers, "CEYREK", "BUY", 1.5)
    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_QUANTITY"
    assert "Çeyrek Altın" in response.json()["message"]
    assert trade(client, auth_headers, "CEYREK", "BUY", 2).status_code == 201
    # gram altın kesirli alınabilir
    assert trade(client, auth_headers, "GRAM", "BUY", 1.25).status_code == 201
