"""Unified Inbox (MOD-06) with the suggest-only Customer Engagement Agent (MOD-07A)."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from app.core.db import utcnow
from app.core.deps import Sales
from app.models import Conversation, Customer, Message, PolicyDecision, WorkspaceMember
from app.social.engagement import run_agent, send_outbound

router = APIRouter(prefix="/conversations", tags=["inbox"])


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ConversationOut(ORM):
    id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str = ""
    channel: str
    status: str
    assigned_user_id: uuid.UUID | None
    last_message_at: datetime | None
    last_customer_message_at: datetime | None
    last_message_preview: str = ""
    automation_paused: bool
    ai_intent: str | None
    ai_confidence: float | None
    ai_summary: str | None
    ai_suggested_reply: str | None
    ai_needs_human: bool
    ai_flags: list
    ai_updated_at: datetime | None
    needs_ai_at: datetime | None


class MessageOut(ORM):
    id: uuid.UUID
    direction: str
    actor: str
    text: str
    provider_status: str
    error: str | None
    created_at: datetime


class DecisionOut(ORM):
    id: uuid.UUID
    decision: str
    reasons: list
    purpose: str
    actor: str
    hold_until: datetime | None
    created_at: datetime


class ConversationDetail(ConversationOut):
    messages: list[MessageOut]
    decisions: list[DecisionOut]


class ReplyIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    from_suggestion: bool = False


class ReplyOut(BaseModel):
    message: MessageOut | None
    decision: DecisionOut


class ConversationPatch(BaseModel):
    status: Literal["open", "pending", "resolved"] | None = None
    assigned_user_id: uuid.UUID | None = None
    automation_paused: bool | None = None


def _out(db, conv: Conversation, cls=ConversationOut, **extra):
    customer = db.get(Customer, conv.customer_id)
    last = db.scalar(
        select(Message.text)
        .where(Message.conversation_id == conv.id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    return cls.model_validate(
        {
            **{k: getattr(conv, k) for k in ConversationOut.model_fields if hasattr(conv, k)},
            "customer_name": customer.display_name,
            "last_message_preview": (last or "")[:140],
            **extra,
        }
    )


@router.get("", response_model=list[ConversationOut])
def list_conversations(
    ctx: Sales,
    status_: Annotated[Literal["open", "pending", "resolved"] | None, Query(alias="status")] = None,
    needs_human: bool | None = None,
    q: str | None = None,
    limit: int = 50,
):
    stmt = (
        select(Conversation)
        .join(Customer, Customer.id == Conversation.customer_id)
        .where(Conversation.workspace_id == ctx.ws_id)
        .order_by(Conversation.last_message_at.desc().nulls_last())
        .limit(min(limit, 200))
    )
    if status_:
        stmt = stmt.where(Conversation.status == status_)
    if needs_human is not None:
        stmt = stmt.where(Conversation.ai_needs_human == needs_human)
    if q:
        stmt = stmt.where(func.lower(Customer.display_name).contains(q.lower()))
    return [_out(ctx.db, c) for c in ctx.db.scalars(stmt)]


@router.get("/{conv_id}", response_model=ConversationDetail)
def get_conversation(conv_id: uuid.UUID, ctx: Sales):
    conv = ctx.get(Conversation, conv_id)
    messages = ctx.db.scalars(
        select(Message).where(Message.conversation_id == conv.id).order_by(Message.created_at)
    ).all()
    decisions = ctx.db.scalars(
        select(PolicyDecision)
        .where(PolicyDecision.conversation_id == conv.id)
        .order_by(PolicyDecision.created_at.desc())
        .limit(10)
    ).all()
    return _out(
        ctx.db,
        conv,
        ConversationDetail,
        messages=[MessageOut.model_validate(m) for m in messages],
        decisions=[DecisionOut.model_validate(d) for d in decisions],
    )


@router.post("/{conv_id}/messages", response_model=ReplyOut)
def reply(conv_id: uuid.UUID, body: ReplyIn, ctx: Sales):
    """Human reply (or approved AI suggestion). Still passes the policy engine."""
    conv = ctx.get(Conversation, conv_id)
    msg, decision = send_outbound(
        ctx.db, conv, body.text.strip(), actor="human", purpose="response", user_id=ctx.user.id
    )
    if msg is not None:
        if body.from_suggestion:
            conv.ai_suggested_reply = None
        conv.ai_needs_human = False
    ctx.audit(
        "inbox.reply",
        "conversation",
        conv.id,
        decision=decision.decision,
        from_suggestion=body.from_suggestion,
    )
    ctx.db.commit()
    return ReplyOut(
        message=MessageOut.model_validate(msg) if msg else None,
        decision=DecisionOut.model_validate(decision),
    )


@router.patch("/{conv_id}", response_model=ConversationOut)
def patch_conversation(conv_id: uuid.UUID, body: ConversationPatch, ctx: Sales):
    conv = ctx.get(Conversation, conv_id)
    changes = body.model_dump(exclude_unset=True)
    if (uid := changes.get("assigned_user_id")) is not None and not ctx.db.scalar(
        select(WorkspaceMember.id).where(
            WorkspaceMember.workspace_id == ctx.ws_id, WorkspaceMember.user_id == uid
        )
    ):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "Người được giao không phải thành viên của cửa hàng"
        )
    for k, v in changes.items():
        setattr(conv, k, v)
    ctx.audit("conversation.updated", "conversation", conv.id, fields=sorted(changes))
    ctx.db.commit()
    return _out(ctx.db, conv)


@router.post("/{conv_id}/analyze", response_model=ConversationOut)
def analyze_now(conv_id: uuid.UUID, ctx: Sales):
    """Staff-triggered re-analysis (runs inline; webhook-triggered runs go through the worker)."""
    conv = ctx.get(Conversation, conv_id)
    run_agent(ctx.db, conv, utcnow())
    ctx.db.commit()
    return _out(ctx.db, conv)
