import sqlite3
import uuid
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import DateTime, Engine, Uuid, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from sqlalchemy.types import TypeDecorator

from app.core.config import get_settings


def utcnow() -> datetime:
    return datetime.now(UTC)


class UTCDateTime(TypeDecorator):
    """Always UTC-aware in Python; SQLite drops tzinfo, Postgres keeps it."""

    impl = DateTime(timezone=True)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            raise ValueError("naive datetime not allowed; use UTC-aware values")
        return value.astimezone(UTC) if value is not None else None

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value


class Base(DeclarativeBase):
    type_annotation_map: ClassVar = {datetime: UTCDateTime, uuid.UUID: Uuid}


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(default=utcnow)


@event.listens_for(Engine, "connect")
def _sqlite_foreign_keys(conn, _record) -> None:
    # SQLite ignores ON DELETE CASCADE unless asked; Postgres always enforces it.
    if isinstance(conn, sqlite3.Connection):
        conn.execute("PRAGMA foreign_keys=ON")


def make_engine(url: str):
    if url.startswith("sqlite"):
        kwargs = {"connect_args": {"check_same_thread": False}}
    else:  # poolers (Supabase/Supavisor) drop idle connections: test before use, recycle often
        kwargs = {"pool_pre_ping": True, "pool_recycle": 300}
    return create_engine(url, **kwargs)


engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db
