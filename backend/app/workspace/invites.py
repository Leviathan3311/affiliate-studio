"""Invite staff by email: a one-time link that only the invited address can accept."""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select

from app.core import mail
from app.core.config import get_settings
from app.core.db import utcnow
from app.core.deps import DB, Admin, CurrentUser
from app.core.plan import _aware
from app.models import Brand, Invite, WorkspaceMember

router = APIRouter(tags=["invites"])
INVITE_DAYS = 7


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class InviteOut(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    expires_at: datetime


def create_invite(ctx, email: str, role: str, bg: BackgroundTasks) -> InviteOut:
    email = email.lower()
    ctx.db.execute(
        delete(Invite).where(
            Invite.workspace_id == ctx.ws_id, Invite.email == email, Invite.accepted_at.is_(None)
        )
    )
    token = secrets.token_urlsafe(32)
    inv = Invite(
        workspace_id=ctx.ws_id,
        email=email,
        role=role,
        token_hash=_hash(token),
        invited_by=ctx.user.id,
        expires_at=utcnow() + timedelta(days=INVITE_DAYS),
    )
    ctx.db.add(inv)
    ctx.audit("member.invited", "invite", email, role=role)
    ctx.db.commit()
    shop = (
        ctx.db.scalar(select(Brand.name).where(Brand.workspace_id == ctx.ws_id))
        or ctx.workspace.name
    )
    link = f"{get_settings().frontend_url}/invite?token={token}"
    bg.add_task(
        mail.send,
        email,
        f"{ctx.user.full_name or ctx.user.email} mời bạn vào {shop} trên GrowthPilot",
        f"Chào bạn,\n\n{ctx.user.full_name or ctx.user.email} mời bạn cùng quản lý {shop} trên GrowthPilot.\n"
        f"Mở liên kết sau trong {INVITE_DAYS} ngày, đăng ký hoặc đăng nhập bằng email {email}:\n{link}\n",
    )
    return InviteOut(id=inv.id, email=email, role=role, expires_at=inv.expires_at)


@router.get("/workspace/invites", response_model=list[InviteOut])
def list_invites(ctx: Admin):
    rows = ctx.db.scalars(
        select(Invite)
        .where(
            Invite.workspace_id == ctx.ws_id,
            Invite.accepted_at.is_(None),
            Invite.expires_at > utcnow(),
        )
        .order_by(Invite.created_at)
    )
    return [
        InviteOut(id=i.id, email=i.email, role=i.role, expires_at=_aware(i.expires_at))
        for i in rows
    ]


@router.delete("/workspace/invites/{invite_id}", status_code=204)
def cancel_invite(invite_id: uuid.UUID, ctx: Admin):
    ctx.db.delete(ctx.get(Invite, invite_id))
    ctx.db.commit()


def _open(db, token: str) -> Invite:
    inv = db.scalar(select(Invite).where(Invite.token_hash == _hash(token)))
    if inv is None or inv.accepted_at or _aware(inv.expires_at) < utcnow():
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "Lời mời không còn hiệu lực, hãy nhờ người mời gửi lại"
        )
    return inv


class InvitePreview(BaseModel):
    shop: str
    email: str
    role: str


@router.get("/auth/invites/{token}", response_model=InvitePreview)
def preview_invite(token: str, db: DB):
    inv = _open(db, token)
    shop = db.scalar(select(Brand.name).where(Brand.workspace_id == inv.workspace_id)) or ""
    return InvitePreview(shop=shop, email=inv.email, role=inv.role)


class AcceptIn(BaseModel):
    token: str


@router.post("/auth/invites/accept")
def accept_invite(body: AcceptIn, user: CurrentUser, db: DB):
    inv = _open(db, body.token)
    if user.email.lower() != inv.email:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            f"Lời mời này dành cho {inv.email}, hãy đăng nhập bằng email đó",
        )
    if not db.scalar(
        select(WorkspaceMember.id).where(
            WorkspaceMember.workspace_id == inv.workspace_id, WorkspaceMember.user_id == user.id
        )
    ):
        db.add(WorkspaceMember(workspace_id=inv.workspace_id, user_id=user.id, role=inv.role))
    inv.accepted_at = utcnow()
    db.commit()
    return {"workspace_id": inv.workspace_id}
