"""Plans and payments: a free trial, then a monthly price paid by bank transfer (VietQR).

The platform admin confirms each transfer by hand; that extends the workspace's paid_until.
"""

import uuid
from datetime import datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.deps import DB, AnyMember, CurrentUser
from app.core.plan import _aware, access_until, is_active
from app.models import Payment, User, Workspace, WorkspaceMember

router = APIRouter(tags=["billing"])
MONTH = timedelta(days=30)


def transfer_code(ws_id: uuid.UUID) -> str:
    return f"GP {ws_id.hex[:8].upper()}"


class Transfer(BaseModel):
    bank_bin: str
    account: str
    account_name: str
    content: str
    qr_url: str | None


class BillingOut(BaseModel):
    status: str  # trial | active | expired
    access_until: datetime
    price_vnd: int
    transfer: Transfer


@router.get("/billing", response_model=BillingOut)
def billing(ctx: AnyMember):
    s, ws = get_settings(), ctx.workspace
    until = access_until(ws)
    state = "expired" if utcnow() >= until else ("active" if ws.paid_until else "trial")
    content = transfer_code(ws.id)
    qr = None
    if s.bank_bin and s.bank_account:
        q = urlencode(
            {"amount": s.plan_price_vnd, "addInfo": content, "accountName": s.bank_account_name}
        )
        qr = f"https://img.vietqr.io/image/{s.bank_bin}-{s.bank_account}-compact2.png?{q}"
    return BillingOut(
        status=state,
        access_until=until,
        price_vnd=s.plan_price_vnd,
        transfer=Transfer(
            bank_bin=s.bank_bin,
            account=s.bank_account,
            account_name=s.bank_account_name,
            content=content,
            qr_url=qr,
        ),
    )


# --- platform admin (the people who run GrowthPilot, listed in PLATFORM_ADMIN_EMAILS) ---


def is_platform_admin(user: User) -> bool:
    return user.email.lower() in {e.lower() for e in get_settings().platform_admin_emails}


def platform_admin(user: CurrentUser) -> User:
    if not is_platform_admin(user):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ quản trị GrowthPilot")
    return user


PlatformAdmin = Annotated[User, Depends(platform_admin)]


class AdminWorkspace(BaseModel):
    id: uuid.UUID
    name: str
    owner_email: str
    created_at: datetime
    access_until: datetime
    active: bool
    transfer_code: str
    paid_total_vnd: int


class PaymentIn(BaseModel):
    months: int = Field(ge=1, le=36)
    amount_vnd: int = Field(ge=0)
    note: str = Field(default="", max_length=500)


@router.get("/admin/workspaces", response_model=list[AdminWorkspace])
def admin_workspaces(_: PlatformAdmin, db: DB, q: str = ""):
    owner = (
        select(WorkspaceMember.workspace_id, func.min(User.email).label("email"))
        .join(User, User.id == WorkspaceMember.user_id)
        .where(WorkspaceMember.role == "owner")
        .group_by(WorkspaceMember.workspace_id)
        .subquery()
    )
    paid = (
        select(Payment.workspace_id, func.sum(Payment.amount_vnd).label("total"))
        .group_by(Payment.workspace_id)
        .subquery()
    )
    stmt = (
        select(Workspace, owner.c.email, paid.c.total)
        .outerjoin(owner, owner.c.workspace_id == Workspace.id)
        .outerjoin(paid, paid.c.workspace_id == Workspace.id)
        .order_by(Workspace.created_at.desc())
    )
    out = []
    for ws, email, total in db.execute(stmt).all():
        row = AdminWorkspace(
            id=ws.id,
            name=ws.name,
            owner_email=email or "",
            created_at=_aware(ws.created_at),
            access_until=access_until(ws),
            active=is_active(ws),
            transfer_code=transfer_code(ws.id),
            paid_total_vnd=total or 0,
        )
        needle = q.strip().lower()
        if not needle or needle in f"{row.name} {row.owner_email} {row.transfer_code}".lower():
            out.append(row)
    return out


@router.post("/admin/workspaces/{ws_id}/payments", response_model=AdminWorkspace, status_code=201)
def record_payment(ws_id: uuid.UUID, body: PaymentIn, admin: PlatformAdmin, db: DB):
    ws = db.get(Workspace, ws_id)
    if ws is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cửa hàng")
    start = max(utcnow(), access_until(ws))  # paying early adds to the time left
    ws.paid_until = start + MONTH * body.months
    db.add(Payment(workspace_id=ws.id, created_by=admin.id, **body.model_dump()))
    db.commit()
    return next(w for w in admin_workspaces(admin, db) if w.id == ws.id)
