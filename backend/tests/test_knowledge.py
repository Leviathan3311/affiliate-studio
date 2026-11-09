import asyncio

import pytest
from sqlalchemy import select

from app.ai import knowledge
from app.ai.engagement_agent import SYSTEM_PROMPT, render
from app.models import KnowledgeSyncState
from tests.conftest import signup


@pytest.fixture
def fake_rag(monkeypatch):
    """LightRAG stand-in: records inserts/deletes instead of touching Postgres/Gemini."""
    calls = []

    async def insert(ws, doc_id, text):
        calls.append(("insert", doc_id))
        return not doc_id.startswith("knowledge:fail")

    async def delete(ws, doc_id):
        calls.append(("delete", doc_id))

    class Runtime:
        def run(self, coro, timeout):
            return asyncio.run(coro)

    monkeypatch.setattr(knowledge, "enabled", lambda: True)
    monkeypatch.setattr(knowledge, "_runtime", lambda: Runtime())
    monkeypatch.setattr(knowledge, "_insert", insert)
    monkeypatch.setattr(knowledge, "_delete", delete)
    return calls


def test_sync_reindexes_only_changes(client, db, fake_rag):
    h = signup(client)
    import uuid

    ws = uuid.UUID(h["X-Workspace-Id"])
    svc = client.post(
        "/api/v1/services",
        headers=h,
        json={"name": "Peel da", "description": "Không dùng cho bà bầu"},
    ).json()
    faq = client.post(
        "/api/v1/knowledge", headers=h, json={"title": "Đỗ xe", "content": "Có chỗ đỗ xe máy"}
    ).json()

    first = knowledge.sync(db, ws)
    db.commit()
    assert first == {"changed": 3, "removed": 0, "failed": 0}  # brand + service + faq
    assert knowledge.sync(db, ws) == {
        "changed": 0,
        "removed": 0,
    }  # nothing changed: no Gemini calls

    fake_rag.clear()
    client.put(
        f"/api/v1/services/{svc['id']}",
        headers=h,
        json={"name": "Peel da", "description": "Chống chỉ định: phụ nữ mang thai"},
    )
    client.delete(f"/api/v1/knowledge/{faq['id']}", headers=h)
    db.expire_all()
    assert knowledge.sync(db, ws) == {"changed": 1, "removed": 1, "failed": 0}
    db.commit()
    assert fake_rag == [
        ("delete", f"knowledge:{faq['id']}"),
        ("delete", f"service:{svc['id']}"),
        ("insert", f"service:{svc['id']}"),
    ]
    ids = set(db.scalars(select(KnowledgeSyncState.doc_id)))
    assert ids == {"brand", f"service:{svc['id']}"}


def test_build_context_prices_come_from_sql_not_retrieval(client, db, monkeypatch):
    import uuid

    h = signup(client)
    client.post("/api/v1/services", headers=h, json={"name": "Massage", "price_min": 650000})
    monkeypatch.setattr(knowledge, "retrieve", lambda ws, q: "Đối thủ bán massage 199k")
    text, prices = knowledge.build_context(db, uuid.UUID(h["X-Workspace-Id"]), "giá massage")
    assert "650.000đ" in text and "(lightrag;" in text
    assert prices == {650000}  # 199k from retrieved text is never an allowed quote


def test_prompt_template_renders_langfuse_placeholders():
    out = render(
        SYSTEM_PROMPT,
        brand="Lotus",
        industry="tiệm nail",
        tone="nhẹ nhàng",
        forbidden="không hứa",
        intents="a|b",
    )
    assert 'của tiệm nail "Lotus"' in out and "{{" not in out and '{"intent": one of a|b' in out


def test_failed_extraction_is_retried(client, db, fake_rag, monkeypatch):
    import uuid

    h = signup(client)
    ws = uuid.UUID(h["X-Workspace-Id"])
    outcomes = iter([False, True])  # Gemini overloaded once, then fine

    async def flaky(ws_id, doc_id, text):
        return next(outcomes) if doc_id.startswith("knowledge:") else True

    monkeypatch.setattr(knowledge, "_insert", flaky)
    client.post(
        "/api/v1/knowledge",
        headers=h,
        json={"title": "Peel", "content": "Không dùng khi mang thai"},
    )
    assert knowledge.sync(db, ws)["failed"] == 1
    db.commit()
    assert knowledge.sync(db, ws) == {"changed": 1, "removed": 0, "failed": 0}
