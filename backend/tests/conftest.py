import os

os.environ.update(
    GP_ENV_FILE="",
    DATABASE_URL="sqlite://",
    META_APP_SECRET="test-app-secret",
    META_DRY_RUN="true",
    GROQ_API_KEY="",
    GEMINI_API_KEY="",
)

import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core import db as app_db
from app.core.db import Base
from app.main import app


@pytest.fixture
def engine():
    from sqlalchemy import create_engine

    eng = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(eng)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine):
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    with Session() as s:
        yield s


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    from app.core.config import get_settings

    Session = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(app_db, "SessionLocal", Session)  # background tasks + worker
    monkeypatch.setattr(get_settings(), "local_media_dir", str(tmp_path / "media"))

    def override():
        with Session() as s:
            yield s

    app.dependency_overrides[app_db.get_db] = override
    yield TestClient(app)
    app.dependency_overrides.clear()


def signup(client, email="owner@spa.vn", workspace="Lotus Spa"):
    r = client.post("/api/v1/auth/register", json={"email": email, "password": "secret123"})
    assert r.status_code == 201, r.text
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    r = client.post("/api/v1/workspaces", json={"name": workspace}, headers=headers)
    assert r.status_code == 201, r.text
    return {**headers, "X-Workspace-Id": r.json()["id"]}


def connect_page(client, headers, page_id="1234567890"):
    r = client.post(
        "/api/v1/integrations/social-accounts/manual",
        json={"page_id": page_id, "name": "Lotus Page", "page_access_token": "EAAB" + "x" * 40},
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def messenger_payload(page_id, psid, mid, text, ts_ms):
    return {
        "object": "page",
        "entry": [
            {
                "id": page_id,
                "time": ts_ms,
                "messaging": [
                    {
                        "sender": {"id": psid},
                        "recipient": {"id": page_id},
                        "timestamp": ts_ms,
                        "message": {"mid": mid, "text": text},
                    }
                ],
            }
        ],
    }


def post_webhook(client, payload, secret="test-app-secret"):
    body = json.dumps(payload).encode()
    sig = "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return client.post(
        "/api/v1/webhooks/meta",
        content=body,
        headers={"X-Hub-Signature-256": sig, "Content-Type": "application/json"},
    )
