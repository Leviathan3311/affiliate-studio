import hashlib
import uuid

import jwt
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.core import mail
from app.core.config import get_settings
from app.core.deps import DB, CurrentUser
from app.core.security import create_token, decode_token, hash_password, verify_password
from app.models import User, Workspace, WorkspaceMember

router = APIRouter(prefix="/auth", tags=["auth"])


class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)


class Login(BaseModel):
    email: EmailStr
    password: str


class ForgotPassword(BaseModel):
    email: EmailStr


class ResetPassword(BaseModel):
    token: str = Field(max_length=2000)
    password: str = Field(min_length=8, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class WorkspaceRef(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    role: str


class Me(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    workspaces: list[WorkspaceRef]


@router.post("/register", response_model=Token, status_code=201)
def register(body: Register, db: DB):
    email = body.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")
    user = User(email=email, password_hash=hash_password(body.password), full_name=body.full_name)
    db.add(user)
    db.commit()
    return Token(access_token=create_token(str(user.id)))


@router.post("/login", response_model=Token)
def login(body: Login, db: DB):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")
    return Token(access_token=create_token(str(user.id)))


RESET_MINUTES = 30


def _fingerprint(user: User) -> str:
    # Changes with the password, so a reset link works once and dies after any password change.
    return hashlib.sha256(user.password_hash.encode()).hexdigest()[:16]


@router.post("/forgot-password", status_code=202)
def forgot_password(body: ForgotPassword, db: DB, bg: BackgroundTasks):
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is not None:
        token = create_token(
            str(user.id), minutes=RESET_MINUTES, purpose="pw_reset", fp=_fingerprint(user)
        )
        link = f"{get_settings().frontend_url}/reset-password?token={token}"
        bg.add_task(
            mail.send,
            user.email,
            "Đặt lại mật khẩu GrowthPilot",
            f"Chào {user.full_name or 'bạn'},\n\n"
            f"Mở liên kết sau để đặt mật khẩu mới (hết hạn sau {RESET_MINUTES} phút):\n{link}\n\n"
            "Nếu bạn không yêu cầu, hãy bỏ qua email này; mật khẩu cũ vẫn giữ nguyên.",
        )
    # Same answer whether or not the email exists, so this cannot be used to find accounts.
    return {"ok": True}


@router.post("/reset-password", response_model=Token)
def reset_password(body: ResetPassword, db: DB):
    bad = HTTPException(
        status.HTTP_400_BAD_REQUEST, "Liên kết đã hết hạn hoặc đã dùng rồi, hãy gửi lại yêu cầu"
    )
    try:
        claims = decode_token(body.token)
        user = (
            db.get(User, uuid.UUID(claims["sub"])) if claims.get("purpose") == "pw_reset" else None
        )
    except (jwt.PyJWTError, KeyError, ValueError):
        raise bad from None
    if user is None or claims.get("fp") != _fingerprint(user):
        raise bad
    user.password_hash = hash_password(body.password)
    db.commit()
    return Token(access_token=create_token(str(user.id)))


@router.get("/me", response_model=Me)
def me(user: CurrentUser, db: DB):
    rows = db.execute(
        select(Workspace.id, Workspace.name, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(WorkspaceMember.user_id == user.id)
        .order_by(Workspace.created_at)
    ).all()
    return Me(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        workspaces=[WorkspaceRef(id=r.id, name=r.name, role=r.role) for r in rows],
    )
