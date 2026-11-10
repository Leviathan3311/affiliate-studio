import pyotp

from tests.conftest import signup


def test_login_sets_an_httponly_cookie_that_works_without_a_header(client):
    signup(client, "an@spa.vn")
    client.cookies.clear()
    r = client.post("/api/v1/auth/login", json={"email": "an@spa.vn", "password": "secret123"})
    cookie = r.headers["set-cookie"]
    assert "gp_session=" in cookie and "HttpOnly" in cookie and "samesite=lax" in cookie.lower()
    assert client.get("/api/v1/auth/me").json()["email"] == "an@spa.vn"  # cookie only
    assert client.post("/api/v1/auth/logout").status_code == 204
    client.cookies.clear()
    assert client.get("/api/v1/auth/me").status_code == 401


def test_two_factor_login_needs_the_code(client):
    h = signup(client, "boss@spa.vn")
    secret = client.get("/api/v1/auth/2fa/setup", headers=h).json()["secret"]
    bad = client.post(
        "/api/v1/auth/2fa/enable", json={"secret": secret, "code": "000000"}, headers=h
    )
    assert bad.status_code == 422
    code = pyotp.TOTP(secret).now()
    assert (
        client.post(
            "/api/v1/auth/2fa/enable", json={"secret": secret, "code": code}, headers=h
        ).status_code
        == 204
    )
    assert client.get("/api/v1/auth/me", headers=h).json()["mfa_enabled"] is True

    client.cookies.clear()
    r = client.post(
        "/api/v1/auth/login", json={"email": "boss@spa.vn", "password": "secret123"}
    ).json()
    assert r["mfa_required"] and r["access_token"] == "" and "gp_session" not in client.cookies
    wrong = client.post(
        "/api/v1/auth/2fa/verify", json={"mfa_token": r["mfa_token"], "code": "123456"}
    )
    assert wrong.status_code == 401
    ok = client.post(
        "/api/v1/auth/2fa/verify",
        json={"mfa_token": r["mfa_token"], "code": pyotp.TOTP(secret).now()},
    )
    assert ok.status_code == 200 and client.get("/api/v1/auth/me").status_code == 200
