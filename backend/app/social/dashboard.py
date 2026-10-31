"""Notifications (MOD-07A.E) and Analytics overview (MOD-11). Internal GrowthPilot metrics only."""

import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter
from pydantic import AwareDatetime, BaseModel, ConfigDict
from sqlalchemy import func, select

from app.core.db import utcnow
from app.core.deps import AnyMember
from app.models import Booking, Conversation, Lead, Message, Notification

router = APIRouter(tags=["dashboard"])


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    type: str
    priority: str
    title: str
    body: str
    conversation_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    read_at: datetime | None
    created_at: datetime


@router.get("/notifications", response_model=list[NotificationOut])
def list_notifications(ctx: AnyMember, unread: bool = False, limit: int = 50):
    stmt = select(Notification).where(Notification.workspace_id == ctx.ws_id)
    if unread:
        stmt = stmt.where(Notification.read_at.is_(None))
    return ctx.db.scalars(
        stmt.order_by(Notification.created_at.desc()).limit(min(limit, 200))
    ).all()


@router.post("/notifications/{notification_id}/acknowledge", response_model=NotificationOut)
def acknowledge(notification_id: uuid.UUID, ctx: AnyMember):
    n = ctx.get(Notification, notification_id)
    n.read_at = n.read_at or utcnow()
    ctx.db.commit()
    return n


class Overview(BaseModel):
    period_start: datetime
    period_end: datetime
    leads_total: int
    leads_by_source: dict[str, int]
    leads_by_status: dict[str, int]
    conversations: int
    conversations_replied: int
    response_rate: float | None
    avg_first_response_minutes: float | None
    needs_human: int
    bookings_total: int
    bookings_by_status: dict[str, int]
    lead_to_booking_rate: float | None
    expected_revenue: int
    actual_revenue: int
    unread_high_intent: int


@router.get("/analytics/overview", response_model=Overview)
def overview(ctx: AnyMember, start: AwareDatetime | None = None, end: AwareDatetime | None = None):
    end = end or utcnow()
    start = start or end - timedelta(days=30)
    db, ws = ctx.db, ctx.ws_id

    def grouped(col, *where) -> dict[str, int]:
        return dict(db.execute(select(col, func.count()).where(*where).group_by(col)).all())

    lead_where = (Lead.workspace_id == ws, Lead.created_at >= start, Lead.created_at < end)
    leads_by_source = grouped(Lead.source, *lead_where)
    leads_total = sum(leads_by_source.values())

    # First inbound vs first successful outbound per conversation (computed in Python: portable).
    first = (
        select(
            Message.conversation_id,
            Message.direction,
            func.min(Message.created_at).label("at"),
        )
        .where(
            Message.workspace_id == ws,
            Message.created_at >= start,
            Message.created_at < end,
            Message.provider_status.in_(("received", "sent", "dry_run")),
            Message.actor != "system",  # the night auto-ack is not a real response
        )
        .group_by(Message.conversation_id, Message.direction)
    )
    firsts: dict = {}
    for conv_id, direction, at in db.execute(first):
        firsts.setdefault(conv_id, {})[direction] = at
    with_inbound = [f for f in firsts.values() if "in" in f]
    gaps = [
        (f["out"] - f["in"]).total_seconds() / 60
        for f in with_inbound
        if "out" in f and f["out"] >= f["in"]
    ]

    b_where = (Booking.workspace_id == ws, Booking.created_at >= start, Booking.created_at < end)
    bookings_by_status = grouped(Booking.status, *b_where)
    bookings_total = sum(bookings_by_status.values())
    booked_leads = db.scalar(
        select(func.count(func.distinct(Booking.lead_id))).where(
            *b_where, Booking.lead_id.is_not(None), Booking.status != "cancelled"
        )
    )
    expected = db.scalar(
        select(func.coalesce(func.sum(Booking.expected_value), 0)).where(
            *b_where, Booking.status.in_(("pending", "confirmed", "arrived", "completed"))
        )
    )
    actual = db.scalar(
        select(func.coalesce(func.sum(Booking.actual_revenue), 0)).where(
            *b_where, Booking.status == "completed"
        )
    )

    return Overview(
        period_start=start,
        period_end=end,
        leads_total=leads_total,
        leads_by_source=leads_by_source,
        leads_by_status=grouped(Lead.status, *lead_where),
        conversations=len(with_inbound),
        conversations_replied=len(gaps),
        response_rate=round(len(gaps) / len(with_inbound), 3) if with_inbound else None,
        avg_first_response_minutes=round(sum(gaps) / len(gaps), 1) if gaps else None,
        needs_human=db.scalar(
            select(func.count()).where(
                Conversation.workspace_id == ws,
                Conversation.ai_needs_human,
                Conversation.status != "resolved",
            )
        ),
        bookings_total=bookings_total,
        bookings_by_status=bookings_by_status,
        lead_to_booking_rate=round(booked_leads / leads_total, 3) if leads_total else None,
        expected_revenue=int(expected),
        actual_revenue=int(actual),
        unread_high_intent=db.scalar(
            select(func.count()).where(
                Notification.workspace_id == ws,
                Notification.type == "customer.intent.high",
                Notification.read_at.is_(None),
            )
        ),
    )


class Today(BaseModel):
    date: str
    timezone: str
    active_start: str
    active_end: str
    inbound_by_hour: list[int]  # 24 local-hour buckets of customer messages today
    queued_for_morning: int  # threads held by quiet hours for the next batch run
    next_batch_at: datetime | None


@router.get("/analytics/today", response_model=Today)
def today(ctx: AnyMember):
    ws, now = ctx.workspace, utcnow()
    tz = ZoneInfo(ws.timezone)
    local_midnight = now.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
    times = ctx.db.scalars(
        select(Message.created_at).where(
            Message.workspace_id == ws.id,
            Message.direction == "in",
            Message.created_at >= local_midnight,
        )
    ).all()
    buckets = [0] * 24
    for t in times:
        buckets[t.astimezone(tz).hour] += 1
    queued = ctx.db.scalars(
        select(Conversation.needs_ai_at).where(
            Conversation.workspace_id == ws.id, Conversation.needs_ai_at > now
        )
    ).all()
    return Today(
        date=local_midnight.date().isoformat(),
        timezone=ws.timezone,
        active_start=ws.active_start,
        active_end=ws.active_end,
        inbound_by_hour=buckets,
        queued_for_morning=len(queued),
        next_batch_at=min(queued) if queued else None,
    )
