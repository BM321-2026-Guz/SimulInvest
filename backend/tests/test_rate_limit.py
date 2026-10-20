"""Issue #40: /api/auth/login deneme sınırı."""

PASSWORD = "gizli-sifre"


def login(client, email="ayse@example.com", password=PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def fail_times(client, n, email="ayse@example.com"):
    for _ in range(n):
        assert login(client, email, "yanlis-sifre").status_code == 401


def test_blocked_after_five_failures_even_with_correct_password(client, auth_headers):
    fail_times(client, 5)
    response = login(client)
    assert response.status_code == 429
    assert response.json()["code"] == "TOO_MANY_ATTEMPTS"
    assert 0 < int(response.headers["Retry-After"]) <= 900


def test_fewer_failures_do_not_block(client, auth_headers):
    fail_times(client, 4)
    assert login(client).status_code == 200


def test_successful_login_resets_counter(client, auth_headers):
    fail_times(client, 4)
    assert login(client).status_code == 200
    fail_times(client, 4)  # sayaç sıfırlandığı için tekrar 4 hak var
    assert login(client).status_code == 200


def test_block_expires_after_window(client, auth_headers, clock):
    fail_times(client, 5)
    assert login(client).status_code == 429
    clock.now += 901
    assert login(client).status_code == 200


def test_retry_after_counts_down(client, auth_headers, clock):
    fail_times(client, 5)
    clock.now += 600
    assert int(login(client).headers["Retry-After"]) == 300


def test_other_account_is_not_locked(client, auth_headers):
    client.post("/api/auth/register", json={"email": "mehmet@example.com", "password": PASSWORD})
    fail_times(client, 5)
    assert login(client).status_code == 429
    assert login(client, "mehmet@example.com").status_code == 200


def test_ip_limit_across_many_emails(client):
    # Var olmayan farklı hesaplara tek IP'den 20 deneme: IP sayacı dolar.
    for i in range(20):
        assert login(client, f"kisi{i}@example.com", "x").status_code == 401
    assert login(client, "yeni@example.com", "x").status_code == 429


def test_email_case_does_not_bypass_limit(client, auth_headers):
    fail_times(client, 5, "AYSE@example.com")
    assert login(client, "ayse@example.com").status_code == 429


def test_register_is_not_rate_limited(client, auth_headers):
    fail_times(client, 5)
    response = client.post(
        "/api/auth/register", json={"email": "yeni@example.com", "password": PASSWORD}
    )
    assert response.status_code == 201
