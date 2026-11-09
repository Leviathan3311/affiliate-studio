from urllib.parse import parse_qs, urlparse

from app.core import mail
from app.core.security import create_token
from tests.conftest import signup


def _request_link(client, monkeypatch, email):
    sent = []
    monkeypatch.setattr(mail, "send", lambda to, subject, body: sent.append((to, body)))
    r = client.post("/api/v1/auth/forgot-password", json={"email": email})
    assert r.status_code == 202
    return sent


def _token(body):
    link = next(w for w in body.split() if "reset-password?token=" in w)
    return parse_qs(urlparse(link).query)["token"][0]


def test_reset_flow_works_once_and_changes_password(client, monkeypatch):
    signup(client, "lan@spa.vn")
    sent = _request_link(client, monkeypatch, "LAN@spa.vn")
    assert [to for to, _ in sent] == ["lan@spa.vn"]
    token = _token(sent[0][1])

    # A reset link is not a login session.
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code
        == 401
    )

    r = client.post("/api/v1/auth/reset-password", json={"token": token, "password": "newpass99"})
    assert r.status_code == 200 and r.json()["access_token"]
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "lan@spa.vn", "password": "secret123"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/v1/auth/login", json={"email": "lan@spa.vn", "password": "newpass99"}
        ).status_code
        == 200
    )

    again = client.post(
        "/api/v1/auth/reset-password", json={"token": token, "password": "other999"}
    )
    assert again.status_code == 400


def test_unknown_email_gets_same_answer_and_no_mail(client, monkeypatch):
    assert _request_link(client, monkeypatch, "nobody@spa.vn") == []


def test_other_tokens_cannot_reset(client):
    h = signup(client, "mai@spa.vn")
    uid = client.get("/api/v1/auth/me", headers=h).json()["id"]
    for token in (create_token(uid), create_token(uid, purpose="meta_oauth"), "garbage"):
        r = client.post(
            "/api/v1/auth/reset-password", json={"token": token, "password": "newpass99"}
        )
        assert r.status_code == 400


def test_oauth_state_is_not_a_session(client):
    h = signup(client, "hoa@spa.vn")
    uid = client.get("/api/v1/auth/me", headers=h).json()["id"]
    state = create_token(uid, minutes=10, purpose="meta_oauth")
    assert (
        client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {state}"}).status_code
        == 401
    )
