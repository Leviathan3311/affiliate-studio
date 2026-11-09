"""When a workspace may use the app: a free trial from creation, extended by confirmed payments."""

from datetime import datetime, timedelta

from app.core.config import get_settings
from app.core.db import utcnow
from app.models import Workspace


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=utcnow().tzinfo)


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=utcnow().tzinfo)


def access_until(ws: Workspace) -> datetime:
    trial_end = _aware(ws.created_at) + timedelta(days=get_settings().trial_days)
    return max(trial_end, _aware(ws.paid_until)) if ws.paid_until else trial_end


def is_active(ws: Workspace) -> bool:
    return utcnow() < access_until(ws)
