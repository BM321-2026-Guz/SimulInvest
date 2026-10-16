def test_register_creates_wallet_with_initial_balance(client, auth_headers):
    # Senaryo 3
    portfolio = client.get("/api/portfolio", headers=auth_headers).json()
    assert portfolio["balance"] == 100000.0
    assert portfolio["holdings"] == []
    assert portfolio["totalProfitLoss"] == 0.0


def test_register_returns_token_and_expiry(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "ali@example.com", "password": "12345678", "displayName": "Ali"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["token"]
    assert body["expiresIn"] == 3600


def test_duplicate_email_is_rejected(client, auth_headers):
    # Senaryo 4 (e-posta büyük/küçük harf farkıyla da aynı sayılır)
    response = client.post(
        "/api/auth/register", json={"email": "AYSE@example.com", "password": "baska-sifre"}
    )
    assert response.status_code == 409
    assert response.json()["code"] == "EMAIL_EXISTS"


def test_short_password_is_rejected(client):
    response = client.post(
        "/api/auth/register", json={"email": "veli@example.com", "password": "kisa"}
    )
    assert response.status_code == 400
    assert response.json()["code"] == "VALIDATION_ERROR"


def test_password_over_72_bytes_is_rejected(client):
    # 40 karakter ama 80 bayt: bcrypt'e ulaşmadan reddedilmeli (500 değil).
    response = client.post(
        "/api/auth/register", json={"email": "veli@example.com", "password": "ş" * 40}
    )
    assert response.status_code == 400


def test_login_success(client, auth_headers):
    response = client.post(
        "/api/auth/login", json={"email": "ayse@example.com", "password": "gizli-sifre"}
    )
    assert response.status_code == 200
    assert response.json()["token"]


def test_login_wrong_password(client, auth_headers):
    # Senaryo 5
    response = client.post(
        "/api/auth/login", json={"email": "ayse@example.com", "password": "yanlis-sifre"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


def test_login_unknown_email(client):
    response = client.post(
        "/api/auth/login", json={"email": "yok@example.com", "password": "12345678"}
    )
    assert response.status_code == 401


def test_protected_endpoint_requires_token(client):
    assert client.get("/api/portfolio").status_code == 401
    bad = {"Authorization": "Bearer bozuk-token"}
    assert client.get("/api/portfolio", headers=bad).status_code == 401


def test_password_is_stored_hashed(client, auth_headers, db_session_factory):
    from app.models import User

    with db_session_factory() as db:
        user = db.query(User).one()
    assert user.password_hash != "gizli-sifre"
    assert user.password_hash.startswith("$2")
