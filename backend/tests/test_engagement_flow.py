from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select

from app.ai import engagement_agent as agent_mod
from app.ai.llm import LLMResult, LLMUnavailable, mask_pii
from app.models import Conversation, Customer, Lead, Message, Notification, WebhookEvent
from app.social.engagement import ingest_event, run_agent
from tests.conftest import connect_page, messenger_payload, post_webhook, signup

PAGE = "1234567890"
DAY = datetime(2026, 10, 31, 3, 0, tzinfo=UTC)  # 10:00 VN
NIGHT = datetime(2026, 10, 31, 16, 30, tzinfo=UTC)  # 23:30 VN
MORNING = datetime(2026, 11, 1, 1, 0, tzinfo=UTC)  # 08:00 VN


@pytest.fixture
def llm(monkeypatch):
    """Fake LLM: tests set `llm.reply`; calls are counted."""

    class Fake:
        calls: list = []
        data = {
            "intent": "booking_request",
            "confidence": 0.9,
            "lead_score": 80,
            "summary": "Khách muốn đặt lịch chăm sóc da",
            "reply": "Dạ chăm sóc da cơ bản bên em giá 450.000đ ạ. Chị muốn đặt khung giờ nào?",
            "needs_human": False,
            "reason": "hỏi giá và đặt lịch",
        }

    def fake(db, *, system, user, purpose, workspace_id, **_):
        Fake.calls.append(user)
        return LLMResult(dict(Fake.data), "fake", "fake-model")

    Fake.calls = []
    monkeypatch.setattr(agent_mod, "complete_json", fake)
    return Fake


@pytest.fixture
def spa(client):
    h = signup(client)
    connect_page(client, h, PAGE)
    r = client.post(
        "/api/v1/services",
        json={"name": "Chăm sóc da cơ bản", "duration_minutes": 60, "price_min": 450000},
        headers=h,
    )
    assert r.status_code == 201
    return h


def deliver(client, db, mid, text, at, psid="psid-1"):
    r = post_webhook(client, messenger_payload(PAGE, psid, mid, text, int(at.timestamp() * 1000)))
    assert r.status_code == 200 and r.text == "EVENT_RECEIVED"
    for ev in db.scalars(select(WebhookEvent).where(WebhookEvent.status == "pending")):
        ingest_event(db, ev, now=at)
    db.commit()


def test_webhook_rejects_bad_signature(client, spa):
    r = post_webhook(client, messenger_payload(PAGE, "p", "m", "hi", 1), secret="wrong")
    assert r.status_code == 403


def test_webhook_verify_handshake(client):
    q = "hub.mode=subscribe&hub.verify_token=growthpilot-verify&hub.challenge=42"
    assert client.get(f"/api/v1/webhooks/meta?{q}").text == "42"
    assert (
        client.get(
            "/api/v1/webhooks/meta?hub.mode=subscribe&hub.verify_token=x&hub.challenge=1"
        ).status_code
        == 403
    )


def test_duplicate_delivery_creates_one_customer_and_message(client, db, spa, llm):
    deliver(client, db, "mid.1", "Cho em hỏi giá chăm sóc da", DAY)
    deliver(client, db, "mid.1", "Cho em hỏi giá chăm sóc da", DAY)  # Meta retry
    deliver(client, db, "mid.2", "Còn slot chiều nay không ạ", DAY)
    assert db.scalar(select(func.count()).select_from(WebhookEvent)) == 2
    assert db.scalar(select(func.count()).select_from(Customer)) == 1
    assert db.scalar(select(func.count()).select_from(Lead)) == 1
    assert db.scalar(select(func.count()).select_from(Message)) == 2
    conv = db.scalar(select(Conversation))
    assert conv.needs_ai_at == DAY  # daytime: analyse immediately


def test_daytime_agent_suggests_and_raises_high_intent_once(client, db, spa, llm):
    deliver(client, db, "mid.1", "Em muốn đặt lịch chăm sóc da", DAY)
    conv = db.scalar(select(Conversation))
    run_agent(db, conv, DAY)
    run_agent(db, conv, DAY + timedelta(hours=1))  # same intent same day -> no second alert
    db.commit()
    assert conv.ai_intent == "booking_request" and not conv.ai_needs_human
    assert "450.000đ" in conv.ai_suggested_reply
    assert db.scalar(select(Lead)).status == "qualified"
    assert db.scalar(select(func.count()).select_from(Notification)) == 1
    # suggest mode: nothing was sent automatically
    assert db.scalar(select(func.count()).where(Message.direction == "out")) == 0


def test_unverified_price_forces_human_review(client, db, spa, llm):
    llm.data = {**llm.data, "reply": "Dạ hiện bên em giảm còn 199k thôi ạ"}
    deliver(client, db, "mid.1", "Có giảm giá không", DAY)
    conv = db.scalar(select(Conversation))
    run_agent(db, conv, DAY)
    assert conv.ai_needs_human and conv.ai_flags == ["unverified_price"]


def test_night_messages_get_one_ack_and_one_batched_llm_call(client, db, spa, llm):
    deliver(client, db, "mid.1", "Spa ơi", NIGHT)
    deliver(client, db, "mid.2", "Cho em hỏi giá chăm sóc da", NIGHT + timedelta(minutes=3))
    conv = db.scalar(select(Conversation))
    outs = db.scalars(select(Message).where(Message.direction == "out")).all()
    assert len(outs) == 1 and outs[0].actor == "system"  # static template, zero LLM
    assert "08:00" in outs[0].text and outs[0].provider_status == "dry_run"
    assert llm.calls == [] and conv.needs_ai_at == MORNING

    run_agent(db, conv, MORNING)
    assert len(llm.calls) == 1
    assert "Spa ơi" in llm.calls[0] and "hỏi giá" in llm.calls[0]


def test_opt_out_suppresses_and_blocks_human_reply(client, db, spa, llm):
    deliver(client, db, "mid.1", "Đừng nhắn cho tôi nữa", DAY)
    conv = db.scalar(select(Conversation))
    assert conv.automation_paused and conv.needs_ai_at is None
    r = client.post(f"/api/v1/conversations/{conv.id}/messages", json={"text": "Dạ"}, headers=spa)
    assert r.status_code == 200
    assert r.json()["message"] is None
    assert r.json()["decision"]["reasons"] == ["customer_opted_out"]


def test_human_reply_goes_through_policy_and_is_recorded(client, db, spa, llm):
    now = datetime.now(UTC)
    deliver(client, db, "mid.1", "Hello", now)
    conv = db.scalar(select(Conversation))
    r = client.post(
        f"/api/v1/conversations/{conv.id}/messages", json={"text": "Dạ chào chị"}, headers=spa
    )
    body = r.json()
    assert body["decision"]["decision"] == "ALLOW"
    assert body["message"]["provider_status"] == "dry_run"
    detail = client.get(f"/api/v1/conversations/{conv.id}", headers=spa).json()
    # ignore the quiet-hours auto-ack, which depends on the wall clock when the test runs
    human = [m["direction"] for m in detail["messages"] if m["actor"] != "system"]
    assert human == ["in", "out"]


def test_llm_outage_escalates_to_human(client, db, spa, monkeypatch):
    def boom(*a, **k):
        raise LLMUnavailable("groq: 429; gemini: 503")

    monkeypatch.setattr(agent_mod, "complete_json", boom)
    deliver(client, db, "mid.1", "Hello", DAY)
    conv = db.scalar(select(Conversation))
    run_agent(db, conv, DAY)
    assert conv.ai_needs_human and conv.ai_flags == ["llm_unavailable"]


def test_other_workspace_cannot_read_conversation(client, db, spa, llm):
    deliver(client, db, "mid.1", "Hello", DAY)
    conv = db.scalar(select(Conversation))
    other = signup(client, email="b@spa.vn", workspace="Other Spa")
    assert client.get(f"/api/v1/conversations/{conv.id}", headers=other).status_code == 404
    assert client.get("/api/v1/conversations", headers=other).json() == []
    spoofed = {**other, "X-Workspace-Id": spa["X-Workspace-Id"]}
    assert client.get("/api/v1/conversations", headers=spoofed).status_code == 404


def test_mask_pii():
    assert mask_pii("sđt 0912 345 678, mail a.b@x.vn") == "sđt [SĐT], mail [EMAIL]"
    assert mask_pii("+84912345678") == "[SĐT]"


def test_today_counts_night_queue(client, db, spa, llm):
    now = datetime.now(UTC)
    deliver(client, db, "mid.1", "Hello", now)
    conv = db.scalar(select(Conversation))
    conv.needs_ai_at = now + timedelta(hours=3)  # as if held by quiet hours
    db.commit()
    body = client.get("/api/v1/analytics/today", headers=spa).json()
    assert sum(body["inbound_by_hour"]) == 1 and len(body["inbound_by_hour"]) == 24
    assert body["queued_for_morning"] == 1


def test_worker_survives_a_database_outage(monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app import worker

    calls = []

    def run_once():
        calls.append(1)
        if len(calls) == 1:
            raise OperationalError("select 1", {}, Exception("dns"))
        if len(calls) == 3:
            raise SystemExit  # stop the endless loop after it carried on
        return 1

    monkeypatch.setattr(worker, "run_once", run_once)
    monkeypatch.setattr(worker.time, "sleep", lambda s: None)
    monkeypatch.setattr(worker, "flush", lambda: None)
    try:
        worker.main()
    except SystemExit:
        pass
    assert len(calls) == 3


def test_high_intent_is_emailed_to_the_team_once(client, db, spa, llm, monkeypatch):
    from app.core import mail

    sent = []
    monkeypatch.setattr(mail, "send", lambda to, subject, body: sent.append((to, subject)))
    deliver(client, db, "mid.9", "Em muốn đặt lịch chăm sóc da", DAY)
    conv = db.scalar(select(Conversation))
    run_agent(db, conv, DAY)
    run_agent(db, conv, DAY + timedelta(hours=1))
    assert len(sent) == 1 and sent[0][1].startswith("Khách muốn mua")
