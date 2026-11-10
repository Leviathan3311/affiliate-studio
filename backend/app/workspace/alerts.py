"""Emails to a shop's team for things that cannot wait until someone opens the app."""

import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import mail
from app.core.config import get_settings
from app.core.db import utcnow
from app.core.plan import access_until
from app.models import Brand, Notification, User, Workspace, WorkspaceMember


def team_emails(db: Session, ws_id: uuid.UUID, roles: tuple[str, ...]) -> list[str]:
    return list(
        db.scalars(
            select(User.email)
            .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
            .where(WorkspaceMember.workspace_id == ws_id, WorkspaceMember.role.in_(roles))
        )
    )


def email_team(
    db: Session, ws_id: uuid.UUID, roles: tuple[str, ...], subject: str, body: str
) -> None:
    for to in team_emails(db, ws_id, roles):
        mail.send(to, subject, body)


def _notify_once(db: Session, ws: Workspace, key: str, title: str, body: str) -> bool:
    if db.scalar(
        select(Notification.id).where(
            Notification.workspace_id == ws.id, Notification.dedupe_key == key
        )
    ):
        return False
    db.add(
        Notification(
            workspace_id=ws.id, type="plan", priority="high", title=title, body=body, dedupe_key=key
        )
    )
    return True


def remind_plans(db: Session) -> int:
    """3 days before the trial or paid period ends, and on the day it ends: one email + one notice each."""
    now, sent = utcnow(), 0
    link = f"{get_settings().frontend_url}/app/billing"
    for ws in db.scalars(select(Workspace)):
        until = access_until(ws)
        day = until.date().isoformat()
        brand = db.scalar(select(Brand.name).where(Brand.workspace_id == ws.id)) or ws.name
        if now < until <= now + timedelta(days=3):
            key, title = (
                f"plan:due:{day}",
                f"Gói của {brand} hết hạn ngày {until.strftime('%d/%m')}",
            )
            body = f"Gia hạn trước ngày {until.strftime('%d/%m/%Y')} để AI không ngừng trả lời khách: {link}"
        elif until <= now < until + timedelta(days=1):
            key, title = f"plan:expired:{day}", f"Gói của {brand} đã hết hạn"
            body = f"Tin nhắn của khách vẫn được lưu nhưng AI đã tạm ngừng. Gia hạn để dùng tiếp: {link}"
        else:
            continue
        if _notify_once(db, ws, key, title, body):
            db.commit()
            email_team(db, ws.id, ("owner",), title, f"Chào bạn,\n\n{body}\n\nGrowthPilot")
            sent += 1
    return sent
