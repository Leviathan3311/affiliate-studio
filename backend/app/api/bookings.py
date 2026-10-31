"""Booking & Appointment (MOD-09): manual booking with slot/capacity check."""

import uuid
from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from app.deps import Sales
from app.models import (
    BOOKING_STATUSES,
    Booking,
    BookingStatusHistory,
    Branch,
    Conversation,
    Customer,
    Lead,
    Service,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])
BookingStatus = Literal[BOOKING_STATUSES]  # type: ignore[valid-type]
ACTIVE = ("pending", "confirmed", "arrived")
TRANSITIONS = {
    "pending": {"confirmed", "cancelled"},
    "confirmed": {"arrived", "cancelled", "no_show"},
    "arrived": {"completed"},
}


class BookingIn(BaseModel):
    customer_id: uuid.UUID
    branch_id: uuid.UUID
    service_id: uuid.UUID
    start_at: AwareDatetime
    status: Literal["pending", "confirmed"] = "pending"
    conversation_id: uuid.UUID | None = None
    expected_value: int | None = Field(default=None, ge=0)
    notes: str = Field(default="", max_length=2000)


class BookingPatch(BaseModel):
    status: BookingStatus | None = None
    actual_revenue: int | None = Field(default=None, ge=0)
    notes: str | None = Field(default=None, max_length=2000)


class BookingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str = ""
    branch_id: uuid.UUID
    service_id: uuid.UUID
    service_name: str = ""
    conversation_id: uuid.UUID | None
    start_at: datetime
    end_at: datetime
    status: str
    source: str
    expected_value: int | None
    actual_revenue: int | None
    notes: str
    created_at: datetime


def _out(db, b: Booking) -> BookingOut:
    return BookingOut.model_validate(b).model_copy(
        update={
            "customer_name": db.get(Customer, b.customer_id).display_name,
            "service_name": db.get(Service, b.service_id).name,
        }
    )


def _set_lead(db, customer_id: uuid.UUID, lead_status: str) -> Lead | None:
    lead = db.scalar(
        select(Lead).where(Lead.customer_id == customer_id).order_by(Lead.created_at.desc())
    )
    if lead and lead.status not in ("opted_out", "booked"):
        lead.status = lead_status
    return lead


@router.get("", response_model=list[BookingOut])
def list_bookings(
    ctx: Sales,
    start: AwareDatetime | None = None,
    end: AwareDatetime | None = None,
    branch_id: uuid.UUID | None = None,
    status_: Annotated[BookingStatus | None, Query(alias="status")] = None,
):
    stmt = select(Booking).where(Booking.workspace_id == ctx.ws_id)
    if start:
        stmt = stmt.where(Booking.start_at >= start)
    if end:
        stmt = stmt.where(Booking.start_at < end)
    if branch_id:
        stmt = stmt.where(Booking.branch_id == branch_id)
    if status_:
        stmt = stmt.where(Booking.status == status_)
    return [_out(ctx.db, b) for b in ctx.db.scalars(stmt.order_by(Booking.start_at).limit(500))]


@router.post("", response_model=BookingOut, status_code=201)
def create_booking(body: BookingIn, ctx: Sales):
    db = ctx.db
    customer = ctx.get(Customer, body.customer_id)
    service = ctx.get(Service, body.service_id)
    branch = ctx.get(Branch, body.branch_id)
    if body.conversation_id:
        ctx.get(Conversation, body.conversation_id)
    start = body.start_at
    end = start + timedelta(minutes=service.duration_minutes)

    if branch.capacity:
        if db.get_bind().dialect.name == "postgresql":
            db.execute(select(Branch.id).where(Branch.id == branch.id).with_for_update())
        overlapping = db.scalar(
            select(func.count()).where(
                Booking.branch_id == branch.id,
                Booking.status.in_(ACTIVE),
                Booking.start_at < end,
                Booking.end_at > start,
            )
        )
        if overlapping >= branch.capacity:
            raise HTTPException(
                status.HTTP_409_CONFLICT,
                f"Khung giờ đã kín ({overlapping}/{branch.capacity}) tại {branch.name}",
            )

    lead = _set_lead(db, customer.id, "booked" if body.status == "confirmed" else "booking_pending")
    b = Booking(
        workspace_id=ctx.ws_id,
        customer_id=customer.id,
        branch_id=branch.id,
        service_id=service.id,
        lead_id=lead.id if lead else None,
        conversation_id=body.conversation_id,
        start_at=start,
        end_at=end,
        status=body.status,
        source="messenger" if body.conversation_id else "manual",
        expected_value=body.expected_value
        if body.expected_value is not None
        else service.price_min,
        notes=body.notes,
        created_by=ctx.user.id,
    )
    db.add(b)
    db.flush()
    db.add(BookingStatusHistory(booking_id=b.id, to_status=b.status, changed_by=ctx.user.id))
    ctx.audit("booking.created", "booking", b.id, status=b.status)
    db.commit()
    return _out(db, b)


@router.patch("/{booking_id}", response_model=BookingOut)
def patch_booking(booking_id: uuid.UUID, body: BookingPatch, ctx: Sales):
    b = ctx.get(Booking, booking_id)
    if body.status and body.status != b.status:
        if body.status not in TRANSITIONS.get(b.status, set()):
            raise HTTPException(
                status.HTTP_409_CONFLICT, f"Không thể chuyển {b.status} → {body.status}"
            )
        ctx.db.add(
            BookingStatusHistory(
                booking_id=b.id, from_status=b.status, to_status=body.status, changed_by=ctx.user.id
            )
        )
        ctx.audit("booking.status_changed", "booking", b.id, before=b.status, after=body.status)
        b.status = body.status
        if b.status == "confirmed":
            _set_lead(ctx.db, b.customer_id, "booked")
    if body.actual_revenue is not None:
        if b.status != "completed":
            raise HTTPException(
                status.HTTP_409_CONFLICT, "Chỉ ghi doanh thu khi booking đã hoàn tất"
            )
        b.actual_revenue = body.actual_revenue
        ctx.audit("booking.revenue_recorded", "booking", b.id, amount=body.actual_revenue)
    if body.notes is not None:
        b.notes = body.notes
    ctx.db.commit()
    return _out(ctx.db, b)
