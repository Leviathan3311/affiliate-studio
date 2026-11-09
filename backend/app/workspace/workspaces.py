import logging
import uuid
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator
from sqlalchemy import delete, func, select

from app.core import storage
from app.core.deps import DB, Admin, AnyMember, CurrentUser, Owner
from app.models import ROLES, Booking, Brand, PublishingJob, User, Workspace, WorkspaceMember

router = APIRouter(tags=["workspaces"])
log = logging.getLogger(__name__)
Role = Literal[ROLES]  # type: ignore[valid-type]
HHMM = Annotated[str, StringConstraints(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")]


class WorkspaceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WorkspaceDelete(BaseModel):
    name: str  # typed by the owner as confirmation


class WorkspaceSettings(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    timezone: str
    active_start: str
    active_end: str
    reply_mode: Literal["suggest", "auto"]
    auto_reply_min_confidence: float
    quiet_hours_template: str
    role: str = ""


class SettingsPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    timezone: str | None = None
    active_start: HHMM | None = None
    active_end: HHMM | None = None
    reply_mode: Literal["suggest", "auto"] | None = None
    auto_reply_min_confidence: float | None = Field(default=None, ge=0.5, le=1)
    quiet_hours_template: str | None = Field(default=None, max_length=1000)

    @field_validator("timezone")
    @classmethod
    def valid_tz(cls, v):
        if v is not None:
            try:
                ZoneInfo(v)
            except ZoneInfoNotFoundError:
                raise ValueError("unknown timezone") from None
        return v


class MemberOut(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    role: str


class MemberAdd(BaseModel):
    email: EmailStr
    role: Role


class MemberPatch(BaseModel):
    role: Role


def _settings(ws: Workspace, role: str) -> WorkspaceSettings:
    return WorkspaceSettings.model_validate(ws).model_copy(update={"role": role})


@router.post("/workspaces", response_model=WorkspaceSettings, status_code=201)
def create_workspace(body: WorkspaceCreate, user: CurrentUser, db: DB):
    ws = Workspace(name=body.name)
    db.add(ws)
    db.flush()
    db.add(WorkspaceMember(workspace_id=ws.id, user_id=user.id, role="owner"))
    db.add(Brand(workspace_id=ws.id, name=body.name))
    db.commit()
    return _settings(ws, "owner")


@router.get("/workspace", response_model=WorkspaceSettings)
def get_workspace(ctx: AnyMember):
    return _settings(ctx.workspace, ctx.role)


@router.patch("/workspace", response_model=WorkspaceSettings)
def patch_workspace(body: SettingsPatch, ctx: Admin):
    changes = body.model_dump(exclude_unset=True, exclude_none=True)
    for k, v in changes.items():
        setattr(ctx.workspace, k, v)
    ctx.audit("workspace.settings_updated", "workspace", ctx.ws_id, fields=sorted(changes))
    ctx.db.commit()
    return _settings(ctx.workspace, ctx.role)


@router.delete("/workspace", status_code=204)
def delete_workspace(body: WorkspaceDelete, ctx: Owner, bg: BackgroundTasks):
    """Owner only. Every workspace row goes with it (ON DELETE CASCADE), then its media files."""
    if body.name.strip() != ctx.workspace.name.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Tên spa nhập vào chưa đúng")
    ws_id = ctx.ws_id
    # These hold RESTRICT keys to rows the cascade also removes; Postgres may check them first.
    for model in (Booking, PublishingJob):
        ctx.db.execute(delete(model).where(model.workspace_id == ws_id))
    ctx.db.delete(ctx.workspace)
    ctx.db.commit()
    log.warning("workspace %s deleted by user %s", ws_id, ctx.user.id)
    bg.add_task(storage.delete_prefix, f"ws/{ws_id}/")


@router.get("/workspace/members", response_model=list[MemberOut])
def list_members(ctx: AnyMember):
    rows = ctx.db.execute(
        select(User, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.user_id == User.id)
        .where(WorkspaceMember.workspace_id == ctx.ws_id)
        .order_by(WorkspaceMember.created_at)
    ).all()
    return [MemberOut(user_id=u.id, email=u.email, full_name=u.full_name, role=r) for u, r in rows]


@router.post("/workspace/members", response_model=MemberOut, status_code=201)
def add_member(body: MemberAdd, ctx: Admin):
    # shortcut: adds an already-registered user; email invitations need an email provider.
    if body.role == "owner" and ctx.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ chủ spa mới giao được quyền chủ spa")
    user = ctx.db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Người dùng chưa đăng ký tài khoản")
    exists = ctx.db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == ctx.ws_id, WorkspaceMember.user_id == user.id
        )
    )
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "Đã là thành viên")
    ctx.db.add(WorkspaceMember(workspace_id=ctx.ws_id, user_id=user.id, role=body.role))
    ctx.audit("member.added", "user", user.id, role=body.role)
    ctx.db.commit()
    return MemberOut(user_id=user.id, email=user.email, full_name=user.full_name, role=body.role)


def _member(ctx, user_id: uuid.UUID) -> WorkspaceMember:
    m = ctx.db.scalar(
        select(WorkspaceMember).where(
            WorkspaceMember.workspace_id == ctx.ws_id, WorkspaceMember.user_id == user_id
        )
    )
    if m is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Không tìm thấy thành viên")
    if m.role == "owner" and ctx.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Không thể đổi quyền của chủ spa")
    return m


def _ensure_owner_remains(ctx, m: WorkspaceMember) -> None:
    if m.role != "owner":
        return
    owners = ctx.db.scalar(
        select(func.count()).where(
            WorkspaceMember.workspace_id == ctx.ws_id, WorkspaceMember.role == "owner"
        )
    )
    if owners <= 1:
        raise HTTPException(status.HTTP_409_CONFLICT, "Spa cần ít nhất một chủ spa")


@router.patch("/workspace/members/{user_id}", response_model=MemberOut)
def update_member(user_id: uuid.UUID, body: MemberPatch, ctx: Admin):
    m = _member(ctx, user_id)
    if body.role == "owner" and ctx.role != "owner":
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Chỉ chủ spa mới giao được quyền chủ spa")
    if body.role != "owner":
        _ensure_owner_remains(ctx, m)
    ctx.audit("member.role_changed", "user", user_id, before=m.role, after=body.role)
    m.role = body.role
    ctx.db.commit()
    u = ctx.db.get(User, user_id)
    return MemberOut(user_id=u.id, email=u.email, full_name=u.full_name, role=m.role)


@router.delete("/workspace/members/{user_id}", status_code=204)
def remove_member(user_id: uuid.UUID, ctx: Admin):
    m = _member(ctx, user_id)
    _ensure_owner_remains(ctx, m)
    ctx.db.delete(m)
    ctx.audit("member.removed", "user", user_id)
    ctx.db.commit()
