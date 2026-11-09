from datetime import timedelta

import pytest

from app.core.config import get_settings
from app.core.db import utcnow
from app.models import Brand, Workspace
from tests.conftest import signup


def _expire(db, ws_id):
    ws = db.get(Workspace, ws_id)
    ws.created_at = utcnow() - timedelta(days=get_settings().trial_days + 1)
    db.commit()


@pytest.fixture
def admin(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "platform_admin_emails", ["boss@growthpilot.vn"])
    r = client.post(
        "/api/v1/auth/register", json={"email": "boss@growthpilot.vn", "password": "secret123"}
    )
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_new_workspace_gets_a_trial_and_transfer_details(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "bank_bin", "970436")
    monkeypatch.setattr(get_settings(), "bank_account", "0123456789")
    h = signup(client)
    b = client.get("/api/v1/billing", headers=h).json()
    assert b["status"] == "trial"
    assert b["transfer"]["content"] == "GP " + h["X-Workspace-Id"].replace("-", "")[:8].upper()
    assert b["transfer"]["qr_url"].startswith("https://img.vietqr.io/image/970436-0123456789-")


def test_expired_workspace_is_blocked_except_billing(client, db):
    import uuid

    h = signup(client)
    _expire(db, uuid.UUID(h["X-Workspace-Id"]))
    r = client.get("/api/v1/services", headers=h)
    assert r.status_code == 402
    assert client.get("/api/v1/billing", headers=h).json()["status"] == "expired"
    assert client.get("/api/v1/workspace", headers=h).status_code == 200


def test_platform_admin_records_payment_and_reopens(client, db, admin):
    import uuid

    h = signup(client)
    ws_id = uuid.UUID(h["X-Workspace-Id"])
    _expire(db, ws_id)
    assert client.get("/api/v1/admin/workspaces", headers=h).status_code == 403
    me = client.get("/api/v1/auth/me", headers=admin).json()
    assert me["is_platform_admin"] is True

    rows = client.get("/api/v1/admin/workspaces", params={"q": "owner@spa"}, headers=admin).json()
    assert [(r["name"], r["active"]) for r in rows] == [("Lotus Spa", False)]
    r = client.post(
        f"/api/v1/admin/workspaces/{ws_id}/payments",
        json={"months": 2, "amount_vnd": 998000, "note": "VCB 09/11"},
        headers=admin,
    )
    assert r.status_code == 201 and r.json()["active"] and r.json()["paid_total_vnd"] == 998000
    assert client.get("/api/v1/services", headers=h).status_code == 200
    b = client.get("/api/v1/billing", headers=h).json()
    assert b["status"] == "active"


def test_industry_is_saved_and_used_by_the_ai(client, db):
    import uuid

    from app.ai.knowledge import sql_facts

    r = client.post("/api/v1/auth/register", json={"email": "nail@x.vn", "password": "secret123"})
    h = {"Authorization": f"Bearer {r.json()['access_token']}"}
    ws = client.post(
        "/api/v1/workspaces", json={"name": "Mây Nail", "industry": "Tiệm nail"}, headers=h
    ).json()
    ws_id = uuid.UUID(ws["id"])
    assert db.query(Brand).filter_by(workspace_id=ws_id).one().industry == "Tiệm nail"
    lines, _ = sql_facts(db, ws_id)
    assert lines[0].startswith("Tiệm nail: Mây Nail.")
