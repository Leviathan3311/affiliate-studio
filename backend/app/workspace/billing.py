"""Plans and payments: a free trial, then a monthly price paid by bank transfer (VietQR).

The platform admin confirms each transfer by hand; that extends the workspace's paid_until.
"""

import hmac
import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.core.config import get_settings
from app.core.db import utcnow
from app.core.deps import DB, AnyMember, CurrentUser
from app.core.plan import _aware, access_until, is_active
from app.models import BankTransaction, Notification, Payment, User, Workspace, WorkspaceMember

router = APIRouter(tags=["billing"])
log = logging.getLogger(__name__)
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
    if (
        not user.totp_secret
    ):  # this account can extend any shop's plan: a password alone is not enough
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, "Tài khoản quản trị cần bật xác thực hai lớp"
        )
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
    extend(db, ws, body.months, body.amount_vnd, body.note, created_by=admin.id)
    db.commit()
    return next(w for w in admin_workspaces(admin, db) if w.id == ws.id)


def extend(db, ws: Workspace, months: int, amount: int, note: str, created_by=None) -> None:
    start = max(utcnow(), access_until(ws))  # paying early adds to the time left
    ws.paid_until = start + MONTH * months
    db.add(
        Payment(
            workspace_id=ws.id, months=months, amount_vnd=amount, note=note, created_by=created_by
        )
    )
    until = ws.paid_until.astimezone().strftime("%d/%m/%Y")
    db.add(
        Notification(
            workspace_id=ws.id,
            type="payment",
            title=f"Đã nhận {amount:,}đ, gói dùng được đến hết {until}".replace(",", "."),
            body=note,
            dedupe_key=f"payment:{note}"[:255],
        )
    )


CODE = re.compile(r"GP\s*([0-9A-F]{8})", re.IGNORECASE)


@router.post("/billing/webhooks/sepay")
async def sepay_webhook(request: Request, db: DB, authorization: str = Header(default="")):
    """A bank transfer seen by SePay: 'GP 1A2B3C4D' in its content extends that workspace at once."""
    key = get_settings().sepay_api_key
    if not key or not hmac.compare_digest(authorization, f"Apikey {key}"):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid API key")
    tx = await request.json()
    amount = int(tx.get("transferAmount") or 0)
    if tx.get("transferType") != "in" or amount <= 0:
        return {"success": True}
    ext = f"sepay:{tx.get('id')}"
    if db.scalar(select(BankTransaction.id).where(BankTransaction.external_id == ext)):
        return {"success": True}  # SePay retried a transfer we already recorded
    content = str(tx.get("content") or "")
    row = BankTransaction(
        external_id=ext,
        amount_vnd=amount,
        content=content[:2000],
        reference=str(tx.get("referenceCode") or "")[:64],
        status="unmatched",
    )
    match = CODE.search(content)
    hits = []
    if match:
        code = match.group(1).lower()
        hits = [ws for ws in db.scalars(select(Workspace)) if ws.id.hex.startswith(code)]
    if len(hits) == 1:
        row.workspace_id = hits[0].id
        months = amount // get_settings().plan_price_vnd
        if months >= 1:
            extend(
                db, hits[0], months, amount, f"SePay #{tx.get('id')} · {row.reference} · tự động"
            )
            row.status = "applied"
    db.add(row)
    db.commit()
    if row.status == "unmatched":
        log.warning("sepay %s: %s VND not applied, waiting for the admin", ext, amount)
    return {"success": True}


class BankTxOut(BaseModel):
    id: uuid.UUID
    created_at: datetime
    amount_vnd: int
    content: str
    reference: str
    status: str
    workspace_id: uuid.UUID | None
    workspace_name: str = ""


class AssignIn(BaseModel):
    workspace_id: uuid.UUID
    months: int = Field(ge=1, le=36)


@router.get("/admin/bank-transactions", response_model=list[BankTxOut])
def bank_transactions(_: PlatformAdmin, db: DB, status_: str = Query("unmatched", alias="status")):
    q = select(BankTransaction).order_by(BankTransaction.created_at.desc()).limit(200)
    if status_ != "all":
        q = q.where(BankTransaction.status == status_)
    out = []
    for t in db.scalars(q):
        ws = db.get(Workspace, t.workspace_id) if t.workspace_id else None
        out.append(
            BankTxOut(
                id=t.id,
                created_at=_aware(t.created_at),
                amount_vnd=t.amount_vnd,
                content=t.content,
                reference=t.reference,
                status=t.status,
                workspace_id=t.workspace_id,
                workspace_name=ws.name if ws else "",
            )
        )
    return out


def _unmatched(db, tx_id: uuid.UUID) -> BankTransaction:
    t = db.get(BankTransaction, tx_id)
    if t is None or t.status != "unmatched":
        raise HTTPException(status.HTTP_409_CONFLICT, "Giao dịch này đã được xử lý")
    return t


@router.post("/admin/bank-transactions/{tx_id}/assign", response_model=BankTxOut)
def assign_transaction(tx_id: uuid.UUID, body: AssignIn, admin: PlatformAdmin, db: DB):
    t = _unmatched(db, tx_id)
    ws = db.get(Workspace, body.workspace_id)
    if ws is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy cửa hàng")
    extend(
        db,
        ws,
        body.months,
        t.amount_vnd,
        f"SePay {t.external_id} · {t.reference} · gán tay",
        admin.id,
    )
    t.status, t.workspace_id = "assigned", ws.id
    db.commit()
    return next(x for x in bank_transactions(admin, db, status_="all") if x.id == t.id)


@router.post("/admin/bank-transactions/{tx_id}/ignore", status_code=204)
def ignore_transaction(tx_id: uuid.UUID, _: PlatformAdmin, db: DB):
    _unmatched(db, tx_id).status = "ignored"
    db.commit()
