"""ORM models for the P0 slice (BRD §11). Every business table carries workspace_id."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import JSON, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base, IdMixin

ROLES = ("owner", "admin", "marketing", "sales", "branch_manager")
INTENTS = (
    "price_inquiry",
    "service_inquiry",
    "booking_request",
    "promotion_inquiry",
    "location_inquiry",
    "complaint",
    "other",
    "spam",
)
LEAD_STATUSES = (
    "new",
    "engaged",
    "interested",
    "qualified",
    "booking_pending",
    "booked",
    "not_interested",
    "opted_out",
)
BOOKING_STATUSES = ("pending", "confirmed", "arrived", "completed", "cancelled", "no_show")


def ws_fk() -> Mapped[uuid.UUID]:
    return mapped_column(ForeignKey("workspaces.id", ondelete="CASCADE"), index=True)


# --- Identity (MOD-01) ---
class User(IdMixin, Base):
    __tablename__ = "users"
    email: Mapped[str] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(200), default="")


class Workspace(IdMixin, Base):
    __tablename__ = "workspaces"
    name: Mapped[str] = mapped_column(String(200))
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Ho_Chi_Minh")
    # Customer Engagement active window (system design §3: 08:00-22:00 active)
    active_start: Mapped[str] = mapped_column(String(5), default="08:00")
    active_end: Mapped[str] = mapped_column(String(5), default="22:00")
    reply_mode: Mapped[str] = mapped_column(String(16), default="suggest")  # suggest | auto
    auto_reply_min_confidence: Mapped[float] = mapped_column(default=0.85)
    quiet_hours_template: Mapped[str] = mapped_column(
        Text,
        default=(
            "Cảm ơn anh/chị đã nhắn tin cho {brand}! Hiện chuyên viên tư vấn đã nghỉ ca tối. "
            "Đầu giờ sáng mai ({active_start}) bên em sẽ gửi chi tiết liệu trình và ưu đãi "
            "cho anh/chị nhé ạ!"
        ),
    )


class WorkspaceMember(IdMixin, Base):
    __tablename__ = "workspace_members"
    __table_args__ = (UniqueConstraint("workspace_id", "user_id"),)
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(32))


# --- Organization / Brand (MOD-02) ---
class Brand(IdMixin, Base):
    __tablename__ = "brands"
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True
    )
    name: Mapped[str] = mapped_column(String(200))
    tone_of_voice: Mapped[str] = mapped_column(Text, default="")
    hotline: Mapped[str] = mapped_column(String(32), default="")
    address: Mapped[str] = mapped_column(Text, default="")
    opening_hours: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    forbidden_claims: Mapped[str] = mapped_column(Text, default="")


class Branch(IdMixin, Base):
    __tablename__ = "branches"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(Text, default="")
    # Max concurrent bookings; None = capacity management off (MOD-09)
    capacity: Mapped[int | None]


class Service(IdMixin, Base):
    __tablename__ = "services"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    duration_minutes: Mapped[int] = mapped_column(default=60)
    price_min: Mapped[int | None]  # VND
    price_max: Mapped[int | None]
    promotion: Mapped[str] = mapped_column(Text, default="")
    active: Mapped[bool] = mapped_column(default=True)


class KnowledgeDocument(IdMixin, Base):
    __tablename__ = "knowledge_documents"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    kind: Mapped[str] = mapped_column(String(16), default="faq")  # faq | policy
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)


# --- Social (MOD-06) ---
class SocialAccount(IdMixin, Base):
    __tablename__ = "social_accounts"
    # A Page belongs to exactly one workspace so webhooks route unambiguously.
    __table_args__ = (UniqueConstraint("provider", "external_id"),)
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    provider: Mapped[str] = mapped_column(String(32), default="facebook")
    external_id: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(300), default="")
    token_encrypted: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="connected")


class WebhookEvent(IdMixin, Base):
    __tablename__ = "webhook_events"
    __table_args__ = (UniqueConstraint("provider", "dedupe_key"),)
    provider: Mapped[str] = mapped_column(String(32), default="facebook")
    dedupe_key: Mapped[str] = mapped_column(String(255))
    page_id: Mapped[str] = mapped_column(String(64), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    processed_at: Mapped[datetime | None]


# --- CRM (MOD-08) ---
class Customer(IdMixin, Base):
    __tablename__ = "customers"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    display_name: Mapped[str] = mapped_column(String(200), default="")
    phone: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(320))
    tags: Mapped[list] = mapped_column(JSON, default=list)
    notes: Mapped[str] = mapped_column(Text, default="")
    consent_marketing: Mapped[bool] = mapped_column(default=False)
    # Customer-originated events only (BRD §11 last_interaction_at rule)
    last_interaction_at: Mapped[datetime | None]
    opted_out_at: Mapped[datetime | None]


class CustomerIdentity(IdMixin, Base):
    __tablename__ = "customer_identities"
    __table_args__ = (UniqueConstraint("social_account_id", "external_id"),)
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE")
    )
    external_id: Mapped[str] = mapped_column(String(64))  # page-scoped id (PSID)


class Lead(IdMixin, Base):
    __tablename__ = "leads"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(String(32), default="messenger")
    status: Mapped[str] = mapped_column(String(32), default="new")
    score: Mapped[int] = mapped_column(default=0)
    interested_service_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("services.id", ondelete="SET NULL")
    )
    campaign_ref: Mapped[str | None] = mapped_column(String(100))


# --- Inbox ---
class Conversation(IdMixin, Base):
    __tablename__ = "conversations"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    social_account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("social_accounts.id", ondelete="CASCADE")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    channel: Mapped[str] = mapped_column(String(32), default="messenger")
    status: Mapped[str] = mapped_column(String(16), default="open")  # open|pending|resolved
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    last_customer_message_at: Mapped[datetime | None]
    last_message_at: Mapped[datetime | None] = mapped_column(index=True)
    # When the engagement agent should next analyse this thread (quiet hours push it to 08:00).
    needs_ai_at: Mapped[datetime | None] = mapped_column(index=True)
    night_ack_at: Mapped[datetime | None]
    automation_paused: Mapped[bool] = mapped_column(default=False)
    ai_intent: Mapped[str | None] = mapped_column(String(32))
    ai_confidence: Mapped[float | None]
    ai_summary: Mapped[str | None] = mapped_column(Text)
    ai_suggested_reply: Mapped[str | None] = mapped_column(Text)
    ai_needs_human: Mapped[bool] = mapped_column(default=False)
    ai_flags: Mapped[list] = mapped_column(JSON, default=list)
    ai_updated_at: Mapped[datetime | None]


class Message(IdMixin, Base):
    __tablename__ = "messages"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(8))  # in | out
    actor: Mapped[str] = mapped_column(String(16))  # customer | human | ai | system
    text: Mapped[str] = mapped_column(Text, default="")
    external_id: Mapped[str | None] = mapped_column(String(255), unique=True)
    provider_status: Mapped[str] = mapped_column(String(32), default="received")
    error: Mapped[str | None] = mapped_column(Text)
    sent_by_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    policy_decision_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("engagement_policy_decisions.id", ondelete="SET NULL")
    )


# --- Customer Engagement (MOD-07A) ---
class PolicyDecision(IdMixin, Base):
    __tablename__ = "engagement_policy_decisions"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    decision: Mapped[str] = mapped_column(String(8))  # ALLOW | HOLD | SKIP
    reasons: Mapped[list] = mapped_column(JSON, default=list)
    purpose: Mapped[str] = mapped_column(String(32))
    actor: Mapped[str] = mapped_column(String(16))
    policy_version: Mapped[str] = mapped_column(String(16))
    hold_until: Mapped[datetime | None]


class Suppression(IdMixin, Base):
    __tablename__ = "engagement_suppressions"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    reason: Mapped[str] = mapped_column(String(32))  # opt_out | admin_block | complaint
    source: Mapped[str] = mapped_column(String(32), default="system")
    expires_at: Mapped[datetime | None]


class IntentEvent(IdMixin, Base):
    __tablename__ = "customer_intent_events"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"))
    intent: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float]
    reason: Mapped[str] = mapped_column(Text, default="")


class Notification(IdMixin, Base):
    __tablename__ = "admin_notifications"
    __table_args__ = (UniqueConstraint("workspace_id", "dedupe_key"),)
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    type: Mapped[str] = mapped_column(String(48))
    priority: Mapped[str] = mapped_column(String(8), default="normal")
    title: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text, default="")
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE")
    )
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE")
    )
    dedupe_key: Mapped[str] = mapped_column(String(255))
    read_at: Mapped[datetime | None]


# --- Booking (MOD-09) ---
class Booking(IdMixin, Base):
    __tablename__ = "bookings"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    branch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("branches.id", ondelete="RESTRICT"))
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"))
    customer_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE"), index=True
    )
    lead_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("leads.id", ondelete="SET NULL"))
    conversation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("conversations.id", ondelete="SET NULL")
    )
    start_at: Mapped[datetime] = mapped_column(index=True)
    end_at: Mapped[datetime]
    status: Mapped[str] = mapped_column(String(16), default="pending")
    source: Mapped[str] = mapped_column(String(32), default="manual")
    expected_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 0))
    actual_revenue: Mapped[Decimal | None] = mapped_column(Numeric(14, 0))
    notes: Mapped[str] = mapped_column(Text, default="")
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


class BookingStatusHistory(IdMixin, Base):
    __tablename__ = "booking_status_history"
    booking_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("bookings.id", ondelete="CASCADE"), index=True
    )
    from_status: Mapped[str | None] = mapped_column(String(16))
    to_status: Mapped[str] = mapped_column(String(16))
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )


# --- AI & Governance ---
class AIUsageRecord(IdMixin, Base):
    __tablename__ = "ai_usage_records"
    workspace_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE"), index=True
    )
    purpose: Mapped[str] = mapped_column(String(48))
    provider: Mapped[str] = mapped_column(String(32))
    model: Mapped[str] = mapped_column(String(100))
    latency_ms: Mapped[int] = mapped_column(default=0)
    input_tokens: Mapped[int] = mapped_column(default=0)
    output_tokens: Mapped[int] = mapped_column(default=0)
    success: Mapped[bool] = mapped_column(default=True)
    error: Mapped[str | None] = mapped_column(Text)


class AuditLog(IdMixin, Base):
    __tablename__ = "audit_logs"
    workspace_id: Mapped[uuid.UUID] = ws_fk()
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(64))
    target_type: Mapped[str] = mapped_column(String(48), default="")
    target_id: Mapped[str] = mapped_column(String(64), default="")
    meta: Mapped[dict] = mapped_column(JSON, default=dict)
