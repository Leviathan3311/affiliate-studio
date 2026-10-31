"""Background worker: `uv run python -m app.worker`.

Queue = Postgres rows (webhook_events.status, conversations.needs_ai_at) claimed with
SKIP LOCKED, so several workers can run. Quiet-hours batching falls out of needs_ai_at=08:00.
shortcut: DB polling instead of Redis; move to Redis/Upstash once Kaggle media jobs join the queue.
"""

import json
import logging
import time

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai import knowledge
from app.core.config import get_settings
from app.core.db import SessionLocal, utcnow
from app.core.observability import flush
from app.creative.media import requeue_stale
from app.creative.publishing import due_jobs, run_job
from app.models import Conversation, WebhookEvent, Workspace
from app.social.engagement import ingest_event, run_agent
from app.social.integrations import accept_webhook

log = logging.getLogger("growthpilot.worker")
MAX_ATTEMPTS = 5
BATCH = 50
EDGE_QUEUE = "gp:webhooks"  # same list name as infra/cloudflare/webhook-gateway
AGENT_BATCH = 10  # LLM calls are slow; keep row locks short


def _claim(db: Session, stmt, limit: int):
    if db.get_bind().dialect.name == "postgresql":
        stmt = stmt.with_for_update(skip_locked=True)
    return db.scalars(stmt.limit(limit)).all()


def process_webhooks(db: Session) -> int:
    events = _claim(
        db,
        select(WebhookEvent)
        .where(WebhookEvent.status == "pending")
        .order_by(WebhookEvent.created_at),
        BATCH,
    )
    for ev in events:
        try:
            with db.begin_nested():
                ingest_event(db, ev)
        except Exception as e:  # keep the queue moving; dead-letter after MAX_ATTEMPTS
            log.exception("webhook %s failed", ev.id)
            ev.attempts += 1
            ev.last_error = f"{type(e).__name__}: {e}"[:1000]
            ev.status = "failed" if ev.attempts >= MAX_ATTEMPTS else "pending"
        else:
            ev.processed_at = utcnow()
    db.commit()  # once per batch: committing earlier would release the SKIP LOCKED claims
    return len(events)


def process_agent_queue(db: Session) -> int:
    now = utcnow()
    convs = _claim(
        db,
        select(Conversation)
        .where(Conversation.needs_ai_at.is_not(None), Conversation.needs_ai_at <= now)
        .order_by(Conversation.needs_ai_at),
        AGENT_BATCH,
    )
    for conv in convs:
        try:
            with db.begin_nested():
                run_agent(db, conv, now)
        except Exception:
            log.exception("agent failed for conversation %s", conv.id)
            conv.needs_ai_at, conv.ai_needs_human, conv.ai_flags = None, True, ["agent_error"]
    db.commit()
    return len(convs)


def process_publishing(db: Session) -> int:
    jobs = due_jobs(db)
    for job in jobs:
        try:
            with db.begin_nested():
                run_job(db, job)
        except Exception as e:
            log.exception("publishing job %s failed", job.id)
            job.status, job.last_error = "failed", f"{type(e).__name__}: {e}"[:1000]
    db.commit()
    return len(jobs)


def drain_edge_queue(db: Session) -> int:
    """Deliveries the Cloudflare edge gateway parked in Upstash while this server was off."""
    s = get_settings()
    if not s.upstash_redis_rest_url:
        return 0
    n = 0
    for _ in range(BATCH):
        r = httpx.post(
            s.upstash_redis_rest_url,
            headers={"Authorization": f"Bearer {s.upstash_redis_rest_token}"},
            json=["RPOP", EDGE_QUEUE],
            timeout=10,
        )
        item = r.json().get("result") if r.status_code == 200 else None
        if not item:
            break
        parked = json.loads(item)
        if not accept_webhook(db, parked["body"].encode(), parked.get("sig")):
            log.warning("dropped parked webhook with bad signature")
        n += 1
    db.commit()
    return n


_last_knowledge_sync = 0.0


def sync_knowledge(db: Session) -> int:
    """Re-index changed spa documents into LightRAG (only when content hashes differ)."""
    global _last_knowledge_sync
    if (
        not knowledge.enabled()
        or time.monotonic() - _last_knowledge_sync < get_settings().knowledge_sync_seconds
    ):
        return 0
    _last_knowledge_sync = time.monotonic()
    done = 0
    for ws_id in db.scalars(select(Workspace.id)).all():
        try:
            res = knowledge.sync(db, ws_id)
            db.commit()
            done += res.get("changed", 0) + res.get("removed", 0)
            if res.get("changed") or res.get("removed"):
                log.info("knowledge sync %s: %s", ws_id, res)
        except Exception:
            db.rollback()
            log.exception("knowledge sync failed for %s", ws_id)
    return done


def run_once() -> int:
    with SessionLocal() as db:
        requeue_stale(db)
        db.commit()
        try:
            edge = drain_edge_queue(db)
        except httpx.HTTPError:
            log.warning("upstash unreachable; will retry")
            edge = 0
        return edge + process_webhooks(db) + process_agent_queue(db) + process_publishing(db)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
    poll = get_settings().worker_poll_seconds
    log.info("worker started (poll %.1fs)", poll)
    while True:
        if run_once() == 0:
            time.sleep(poll)
        flush()


if __name__ == "__main__":
    main()
