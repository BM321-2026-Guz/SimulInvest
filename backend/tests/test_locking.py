"""Issue #37: dış fiyat kaynağı yavaşken veritabanı kilidi açık kalmamalı.

Bellek içi test veritabanı tek bağlantı paylaştığı için kilit yarışını gösteremez;
bu testler gerçek bir SQLite dosyası ve ayrı bağlantılar kullanır.
"""

import threading
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db, make_engine
from app.main import app
from app.services.price_service import PriceService, get_price_service

SLOW_FETCH_SECONDS = 5


class SlowPrices:
    """Çağrıldığında `release` sinyaline kadar bekleyen sahte fiyat kaynağı."""

    def __init__(self):
        self.started = threading.Event()
        self.release = threading.Event()

    def __call__(self):
        self.started.set()
        self.release.wait(SLOW_FETCH_SECONDS)
        return {}


@pytest.fixture
def slow_prices():
    return SlowPrices()


@pytest.fixture
def file_client(tmp_path, slow_prices):
    engine = make_engine(f"sqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def _get_db():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    prices = PriceService(slow_prices, cache_seconds=0)
    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_price_service] = lambda: prices
    yield TestClient(app)
    slow_prices.release.set()
    app.dependency_overrides.clear()
    engine.dispose()


def _register(client) -> dict:
    token = client.post(
        "/api/auth/register", json={"email": "kilit@example.com", "password": "gizli-sifre"}
    ).json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize(
    ("method", "path", "body"),
    [
        ("post", "/api/trades", {"symbol": "THYAO", "side": "BUY", "quantity": 1}),
        ("get", "/api/portfolio", None),
    ],
)
def test_slow_price_source_does_not_block_other_requests(
    file_client, slow_prices, method, path, body
):
    headers = _register(file_client)
    if path == "/api/portfolio":
        # Portföyde fiyat sorulması için en az bir varlık olmalı; alımı hızlı kaynakla yap.
        slow_prices.release.set()
        assert (
            file_client.post(
                "/api/trades",
                headers=headers,
                json={"symbol": "THYAO", "side": "BUY", "quantity": 1},
            ).status_code
            == 201
        )
        slow_prices.started.clear()
        slow_prices.release.clear()

    result = {}

    def slow_request():
        call = getattr(TestClient(app), method)
        kwargs = {"headers": headers} | ({"json": body} if body else {})
        result["status"] = call(path, **kwargs).status_code

    worker = threading.Thread(target=slow_request)
    worker.start()
    assert slow_prices.started.wait(5), "Fiyat kaynağı hiç çağrılmadı"

    # Fiyat kaynağı beklerken başka bir istek DB'ye hemen erişebilmeli.
    start = time.monotonic()
    response = TestClient(app).get("/api/transactions", headers=headers)
    elapsed = time.monotonic() - start

    slow_prices.release.set()
    worker.join(10)

    assert response.status_code == 200
    assert elapsed < 1, f"İstek {elapsed:.1f} sn bekledi; fiyat çekilirken DB kilidi açık kalmış"
    assert result["status"] in (200, 201)
