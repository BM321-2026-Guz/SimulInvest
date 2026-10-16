from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db, make_engine
from app.main import app
from app.services.price_service import PriceService, get_price_service


class FakePrices:
    """Testte fiyatları elle belirlemek için sahte kaynak."""

    def __init__(self):
        self.prices: dict[str, Decimal] = {"THYAO": Decimal("300"), "BTC": Decimal("2000000")}

    def __call__(self) -> dict[str, Decimal]:
        return dict(self.prices)


@pytest.fixture
def db_session_factory():
    engine = make_engine("sqlite://", poolclass=StaticPool)
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    engine.dispose()


@pytest.fixture
def fake_prices():
    return FakePrices()


@pytest.fixture
def price_service(fake_prices):
    # cache_seconds=0: her çağrıda fake_prices yeniden okunur, testte fiyat değiştirilebilir.
    return PriceService(fake_prices, cache_seconds=0)


@pytest.fixture
def client(db_session_factory, price_service):
    def _get_db():
        db = db_session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _get_db
    app.dependency_overrides[get_price_service] = lambda: price_service
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    response = client.post(
        "/api/auth/register", json={"email": "ayse@example.com", "password": "gizli-sifre"}
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}"}
