"""Customer engagement pipeline (system design §5.2): ingest -> agent -> policy -> send."""

import re
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.engagement_agent import analyze_conversation
from app.ai.llm import LLMUnavailable
from app.core.db import utcnow
from app.core.observability import trace
from app.core.security import decrypt_secret
from app.models import (
    LEAD_STATUSES,
    Brand,
    Conversation,
    Customer,
    CustomerIdentity,
    IntentEvent,
    Lead,
    Message,
    Notification,
    PolicyDecision,
    SocialAccount,
    Suppression,
    WebhookEvent,
    Workspace,
)
from app.social import meta
from app.social.policy import POLICY_VERSION, ActiveHours, PolicyInput, evaluate

OPT_OUT = re.compile(
    r"\b(stop|unsubscribe)\b|dừng nhắn|ngừng nhắn|không nhận tin|h[uủ]y đăng ký|đừng nhắn",
    re.IGNORECASE,
)
HIGH_INTENTS = {"booking_request", "price_inquiry", "promotion_inquiry"}
HIGH_INTENT_CONFIDENCE = 0.7
HIGH_LEAD_SCORE = 70
# Statuses the agent may move a lead through; terminal/manual ones are never overwritten.
_PROGRESS = LEAD_STATUSES[: LEAD_STATUSES.index("booking_pending")]


def hours_for(ws: Workspace) -> ActiveHours:
    return ActiveHours(ws.timezone, ws.active_start, ws.active_end)


def brand_name(db: Session, ws: Workspace) -> str:
    brand = db.scalar(select(Brand).where(Brand.workspace_id == ws.id))
    return brand.name if brand else ws.name


def is_opted_out(db: Session, customer_id: uuid.UUID, now: datetime) -> bool:
    rows = db.scalars(select(Suppression).where(Suppression.customer_id == customer_id)).all()
    return any(r.expires_at is None or r.expires_at > now for r in rows)


def send_outbound(
    db: Session,
    conv: Conversation,
    text: str,
    *,
    actor: str,
    purpose: str,
    user_id: uuid.UUID | None = None,
    now: datetime | None = None,
) -> tuple[Message | None, PolicyDecision]:
    """The only path to the Send API. Policy is evaluated at execution time, every time."""
    now = now or utcnow()
    ws = db.get(Workspace, conv.workspace_id)
    customer = db.get(Customer, conv.customer_id)
    result = evaluate(
        PolicyInput(
            now=now,
            hours=hours_for(ws),
            purpose=purpose,
            actor=actor,
            last_customer_message_at=conv.last_customer_message_at,
            opted_out=is_opted_out(db, conv.customer_id, now),
            marketing_opt_in=customer.consent_marketing,
            automation_paused=conv.automation_paused,
        )
    )
    decision = PolicyDecision(
        workspace_id=conv.workspace_id,
        conversation_id=conv.id,
        decision=result.decision,
        reasons=result.reasons,
        purpose=purpose,
        actor=actor,
        policy_version=POLICY_VERSION,
        hold_until=result.hold_until,
    )
    db.add(decision)
    db.flush()
    if result.decision != "ALLOW":
        return None, decision

    account = db.get(SocialAccount, conv.social_account_id)
    identity = db.scalar(
        select(CustomerIdentity).where(
            CustomerIdentity.customer_id == conv.customer_id,
            CustomerIdentity.social_account_id == conv.social_account_id,
        )
    )
    sent = meta.send_text(decrypt_secret(account.token_encrypted), identity.external_id, text)
    msg = Message(
        workspace_id=conv.workspace_id,
        conversation_id=conv.id,
        direction="out",
        actor=actor,
        text=text,
        external_id=sent.message_id,
        provider_status=sent.status,
        error=sent.error,
        sent_by_user_id=user_id,
        policy_decision_id=decision.id,
        created_at=now,
    )
    db.add(msg)
    if sent.ok:
        conv.last_message_at = now
    return msg, decision


def _get_or_create_customer(
    db: Session, account: SocialAccount, psid: str
) -> tuple[Customer, bool]:
    identity = db.scalar(
        select(CustomerIdentity).where(
            CustomerIdentity.social_account_id == account.id, CustomerIdentity.external_id == psid
        )
    )
    if identity:
        return db.get(Customer, identity.customer_id), False
    name = meta.fetch_profile_name(decrypt_secret(account.token_encrypted), psid)
    customer = Customer(workspace_id=account.workspace_id, display_name=name or "Khách Messenger")
    db.add(customer)
    db.flush()
    db.add(
        CustomerIdentity(
            workspace_id=account.workspace_id,
            customer_id=customer.id,
            social_account_id=account.id,
            external_id=psid,
        )
    )
    db.add(Lead(workspace_id=account.workspace_id, customer_id=customer.id, source="messenger"))
    return customer, True


def ingest_event(db: Session, event: WebhookEvent, now: datetime | None = None) -> None:
    """Webhook event -> customer/identity/lead/conversation/message. No LLM here."""
    now = now or utcnow()
    account = db.scalar(
        select(SocialAccount).where(
            SocialAccount.provider == event.provider,
            SocialAccount.external_id == event.page_id,
            SocialAccount.status == "connected",
        )
    )
    if account is None:
        event.status = "ignored"
        event.last_error = "page not connected"
        return
    inbound = meta.to_inbound(event.payload)
    if db.scalar(select(Message.id).where(Message.external_id == inbound.mid)):
        event.status = "done"  # delivered twice under different envelopes
        return

    customer, _ = _get_or_create_customer(db, account, inbound.psid)
    conv = db.scalar(
        select(Conversation).where(
            Conversation.social_account_id == account.id, Conversation.customer_id == customer.id
        )
    )
    if conv is None:
        conv = Conversation(
            workspace_id=account.workspace_id, social_account_id=account.id, customer_id=customer.id
        )
        db.add(conv)
        db.flush()

    db.add(
        Message(
            workspace_id=account.workspace_id,
            conversation_id=conv.id,
            direction="in",
            actor="customer",
            text=inbound.text,
            external_id=inbound.mid,
            created_at=inbound.sent_at,
        )
    )
    conv.last_customer_message_at = max(
        filter(None, [conv.last_customer_message_at, inbound.sent_at])
    )
    conv.last_message_at = max(filter(None, [conv.last_message_at, inbound.sent_at]))
    if conv.status == "resolved":
        conv.status = "open"
    customer.last_interaction_at = conv.last_customer_message_at

    if OPT_OUT.search(inbound.text):
        _opt_out(db, customer, conv, now)
        event.status = "done"
        return

    ws = db.get(Workspace, account.workspace_id)
    hours = hours_for(ws)
    if hours.is_active(now):
        conv.needs_ai_at = now
    else:
        # Night mode: zero LLM calls, one static ack per night, batch at the next 08:00.
        conv.needs_ai_at = hours.next_start(now)
        already_acked = (
            conv.night_ack_at and hours.next_start(conv.night_ack_at) == conv.needs_ai_at
        )
        if not already_acked and not conv.automation_paused:
            text = ws.quiet_hours_template.format(
                brand=brand_name(db, ws), active_start=ws.active_start
            )
            db.flush()
            msg, _ = send_outbound(db, conv, text, actor="system", purpose="quiet_ack", now=now)
            if msg is not None:
                conv.night_ack_at = now
    event.status = "done"


def _opt_out(db: Session, customer: Customer, conv: Conversation, now: datetime) -> None:
    db.add(
        Suppression(
            workspace_id=customer.workspace_id,
            customer_id=customer.id,
            reason="opt_out",
            source="customer_message",
        )
    )
    customer.opted_out_at = now
    conv.automation_paused = True
    conv.needs_ai_at = None
    for lead in db.scalars(select(Lead).where(Lead.customer_id == customer.id)):
        lead.status = "opted_out"


def run_agent(db: Session, conv: Conversation, now: datetime | None = None) -> None:
    """Analyse everything the customer sent since the last run in one LLM call."""
    now = now or utcnow()
    conv.needs_ai_at = None
    ws = db.get(Workspace, conv.workspace_id)
    # One Langfuse trace per reply: retrieval -> prompt assembly -> generation (§3.3)
    with trace(
        "customer-reply",
        session_id=str(conv.id),
        user_id=str(conv.customer_id),
        workspace=str(ws.id),
    ) as t:
        try:
            out = analyze_conversation(db, conv, brand_name(db, ws))
        except LLMUnavailable:
            out = False
        t.update(
            output={
                "intent": conv.ai_intent,
                "needs_human": conv.ai_needs_human,
                "flags": conv.ai_flags,
            }
        )
    if out is False:
        conv.ai_needs_human, conv.ai_flags = True, ["llm_unavailable"]
        conv.ai_updated_at = now
        return
    conv.ai_updated_at = now
    if out is None:
        return

    lead = db.scalar(
        select(Lead).where(Lead.customer_id == conv.customer_id).order_by(Lead.created_at.desc())
    )
    if lead and lead.status in _PROGRESS:
        target = "engaged"
        if out.intent == "booking_request":
            target = "qualified" if out.lead_score >= HIGH_LEAD_SCORE else "interested"
        if _PROGRESS.index(target) > _PROGRESS.index(lead.status):
            lead.status = target
        lead.score = max(lead.score, out.lead_score)

    high = (
        out.intent in HIGH_INTENTS and out.confidence >= HIGH_INTENT_CONFIDENCE
    ) or out.lead_score >= HIGH_LEAD_SCORE
    if high:
        _notify_high_intent(db, ws, conv, out, now)

    if (
        ws.reply_mode == "auto"
        and not out.needs_human
        and out.confidence >= ws.auto_reply_min_confidence
        and out.reply
    ):
        send_outbound(db, conv, out.reply, actor="ai", purpose="response", now=now)


def _notify_high_intent(db: Session, ws: Workspace, conv: Conversation, out, now: datetime) -> None:
    db.add(
        IntentEvent(
            workspace_id=ws.id,
            conversation_id=conv.id,
            customer_id=conv.customer_id,
            intent=out.intent,
            confidence=out.confidence,
            reason=out.reason,
        )
    )
    day = now.astimezone(ZoneInfo(ws.timezone)).date().isoformat()
    key = f"intent:{conv.id}:{out.intent}:{day}"  # cooldown: one alert per thread/intent/day
    exists = db.scalar(
        select(Notification.id).where(
            Notification.workspace_id == ws.id, Notification.dedupe_key == key
        )
    )
    if exists:
        return
    customer = db.get(Customer, conv.customer_id)
    db.add(
        Notification(
            workspace_id=ws.id,
            type="customer.intent.high",
            priority="high",
            title=f"{customer.display_name}: {out.intent.replace('_', ' ')}",
            body=out.summary,
            conversation_id=conv.id,
            customer_id=conv.customer_id,
            dedupe_key=key,
        )
    )
