"""CRM & Customer 360 (MOD-08) + leads (MOD-07) + suppressions (MOD-07A.C)."""

import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import func, or_, select

from app.db import utcnow
from app.deps import Sales
from app.models import (
    LEAD_STATUSES,
    Booking,
    Conversation,
    Customer,
    CustomerIdentity,
    Lead,
    Service,
    Suppression,
)

router = APIRouter(tags=["crm"])
LeadStatus = Literal[LEAD_STATUSES]  # type: ignore[valid-type]


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CustomerIn(BaseModel):
    display_name: str = Field(min_length=1, max_length=200)
    phone: str | None = Field(default=None, pattern=r"^\+?\d[\d\s.\-]{7,15}$")
    email: EmailStr | None = None
    tags: list[str] = Field(default_factory=list, max_length=30)
    notes: str = Field(default="", max_length=4000)
    consent_marketing: bool = False


class CustomerPatch(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=200)
    phone: str | None = Field(default=None, pattern=r"^\+?\d[\d\s.\-]{7,15}$")
    email: EmailStr | None = None
    tags: list[str] | None = Field(default=None, max_length=30)
    notes: str | None = Field(default=None, max_length=4000)
    consent_marketing: bool | None = None


class LeadOut(ORM):
    id: uuid.UUID
    customer_id: uuid.UUID
    source: str
    status: str
    score: int
    interested_service_id: uuid.UUID | None
    created_at: datetime


class CustomerOut(ORM):
    id: uuid.UUID
    display_name: str
    phone: str | None
    email: str | None
    tags: list
    notes: str
    consent_marketing: bool
    last_interaction_at: datetime | None
    opted_out_at: datetime | None
    created_at: datetime


class BookingBrief(ORM):
    id: uuid.UUID
    service_id: uuid.UUID
    branch_id: uuid.UUID
    start_at: datetime
    status: str
    expected_value: int | None
    actual_revenue: int | None


class Customer360(CustomerOut):
    channels: list[str]
    leads: list[LeadOut]
    bookings: list[BookingBrief]
    conversation_ids: list[uuid.UUID]


class LeadPatch(BaseModel):
    status: LeadStatus | None = None
    score: int | None = Field(default=None, ge=0, le=100)
    interested_service_id: uuid.UUID | None = None


class SuppressIn(BaseModel):
    reason: Literal["opt_out", "admin_block", "complaint"] = "admin_block"


@router.get("/customers", response_model=list[CustomerOut])
def list_customers(ctx: Sales, q: str | None = None, limit: int = 50, offset: int = 0):
    stmt = select(Customer).where(Customer.workspace_id == ctx.ws_id)
    if q:
        like = f"%{q.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Customer.display_name).like(like),
                Customer.phone.like(f"%{q}%"),
                func.lower(Customer.email).like(like),
            )
        )
    stmt = stmt.order_by(
        Customer.last_interaction_at.desc().nulls_last(), Customer.created_at.desc()
    )
    return ctx.db.scalars(stmt.offset(offset).limit(min(limit, 200))).all()


@router.post("/customers", response_model=CustomerOut, status_code=201)
def create_customer(body: CustomerIn, ctx: Sales):
    c = Customer(workspace_id=ctx.ws_id, **body.model_dump())
    ctx.db.add(c)
    ctx.db.flush()
    ctx.db.add(Lead(workspace_id=ctx.ws_id, customer_id=c.id, source="manual"))
    ctx.audit("customer.created", "customer", c.id)
    ctx.db.commit()
    return c


@router.get("/customers/{customer_id}", response_model=Customer360)
def get_customer(customer_id: uuid.UUID, ctx: Sales):
    c = ctx.get(Customer, customer_id)
    db = ctx.db
    leads = db.scalars(select(Lead).where(Lead.customer_id == c.id).order_by(Lead.created_at)).all()
    bookings = db.scalars(
        select(Booking).where(Booking.customer_id == c.id).order_by(Booking.start_at.desc())
    ).all()
    convs = db.scalars(select(Conversation.id).where(Conversation.customer_id == c.id)).all()
    n_ids = db.scalar(select(func.count()).where(CustomerIdentity.customer_id == c.id))
    return Customer360.model_validate(
        {
            **CustomerOut.model_validate(c).model_dump(),
            "channels": ["messenger"] * bool(n_ids),
            "leads": leads,
            "bookings": bookings,
            "conversation_ids": convs,
        }
    )


@router.patch("/customers/{customer_id}", response_model=CustomerOut)
def patch_customer(customer_id: uuid.UUID, body: CustomerPatch, ctx: Sales):
    c = ctx.get(Customer, customer_id)
    changes = body.model_dump(exclude_unset=True)
    for k, v in changes.items():
        setattr(c, k, v)
    ctx.audit("customer.updated", "customer", c.id, fields=sorted(changes))
    ctx.db.commit()
    return c


@router.post("/customers/{customer_id}/suppressions", response_model=CustomerOut)
def suppress(customer_id: uuid.UUID, body: SuppressIn, ctx: Sales):
    """Stop all automated care for this customer immediately (precedence over every segment)."""
    c = ctx.get(Customer, customer_id)
    ctx.db.add(
        Suppression(workspace_id=ctx.ws_id, customer_id=c.id, reason=body.reason, source="admin")
    )
    if body.reason == "opt_out":
        c.opted_out_at = utcnow()
    for conv in ctx.db.scalars(select(Conversation).where(Conversation.customer_id == c.id)):
        conv.automation_paused, conv.needs_ai_at = True, None
    ctx.audit("customer.suppressed", "customer", c.id, reason=body.reason)
    ctx.db.commit()
    return c


@router.get("/leads", response_model=list[LeadOut])
def list_leads(ctx: Sales, status: LeadStatus | None = None, limit: int = 100):
    stmt = select(Lead).where(Lead.workspace_id == ctx.ws_id)
    if status:
        stmt = stmt.where(Lead.status == status)
    return ctx.db.scalars(stmt.order_by(Lead.created_at.desc()).limit(min(limit, 500))).all()


@router.patch("/leads/{lead_id}", response_model=LeadOut)
def patch_lead(lead_id: uuid.UUID, body: LeadPatch, ctx: Sales):
    lead = ctx.get(Lead, lead_id)
    changes = body.model_dump(exclude_unset=True)
    if changes.get("interested_service_id"):
        ctx.get(Service, changes["interested_service_id"])
    for k, v in changes.items():
        setattr(lead, k, v)
    ctx.audit("lead.updated", "lead", lead.id, **{k: str(v) for k, v in changes.items()})
    ctx.db.commit()
    return lead
