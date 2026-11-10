from urllib.parse import parse_qs, urlparse

from app.core import mail
from tests.conftest import signup


def _register(client, email):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_invite_by_email_only_the_invited_address_can_accept(client, monkeypatch):
    sent = []
    monkeypatch.setattr(mail, "send", lambda to, subject, body: sent.append((to, body)))
    owner = signup(client)
    r = client.post(
        "/api/v1/workspace/members", json={"email": "Lan@Spa.vn", "role": "sales"}, headers=owner
    )
    assert r.status_code == 202 and r.json()["email"] == "lan@spa.vn"
    assert [i["email"] for i in client.get("/api/v1/workspace/invites", headers=owner).json()] == [
        "lan@spa.vn"
    ]
    link = next(w for w in sent[0][1].split() if "invite?token=" in w)
    token = parse_qs(urlparse(link).query)["token"][0]
    assert client.get(f"/api/v1/auth/invites/{token}").json()["shop"] == "Lotus Spa"

    stranger = _register(client, "other@spa.vn")
    assert (
        client.post(
            "/api/v1/auth/invites/accept", json={"token": token}, headers=stranger
        ).status_code
        == 403
    )

    lan = _register(client, "lan@spa.vn")
    r = client.post("/api/v1/auth/invites/accept", json={"token": token}, headers=lan)
    assert r.status_code == 200
    me = client.get("/api/v1/auth/me", headers=lan).json()
    assert [(w["name"], w["role"]) for w in me["workspaces"]] == [("Lotus Spa", "sales")]
    assert (
        client.post("/api/v1/auth/invites/accept", json={"token": token}, headers=lan).status_code
        == 404
    )
    assert client.get("/api/v1/workspace/invites", headers=owner).json() == []


def test_registered_user_is_added_at_once(client):
    owner = signup(client)
    _register(client, "mai@spa.vn")
    r = client.post(
        "/api/v1/workspace/members",
        json={"email": "mai@spa.vn", "role": "marketing"},
        headers=owner,
    )
    assert r.status_code == 201 and r.json()["role"] == "marketing"
