import uuid

import jwt
import pyotp
from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, Response, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.core import mail
from app.core.config import get_settings
from app.core.deps import DB, SESSION_COOKIE, CurrentUser
from app.core.ratelimit import client_ip, limit
from app.core.security import (
    create_token,
    decode_token,
    decrypt_secret,
    encrypt_secret,
    hash_password,
    password_fingerprint,
    session_token,
    verify_password,
)
from app.models import User, Workspace, WorkspaceMember
from app.workspace.billing import is_platform_admin

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
    mfa_required: bool = False
    mfa_token: str = ""


def _signed_in(user: User, response: Response, request: Request) -> Token:
    """Session in an httpOnly cookie for the web app (and in the body for scripts)."""
    token = session_token(user)
    s = get_settings()
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=s.access_token_minutes * 60,
        httponly=True,
        # https in production (Modal sits behind TLS); plain http only for localhost development
        secure=s.env != "dev"
        or request.headers.get("x-forwarded-proto", request.url.scheme) == "https",
        samesite="lax",
    )
    return Token(access_token=token)


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
    is_platform_admin: bool = False
    mfa_enabled: bool = False


@router.post("/register", response_model=Token, status_code=201)
def register(body: Register, db: DB, request: Request, response: Response):
    limit(f"register:{client_ip(request)}", 10, 3600)
    email = body.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Email đã được đăng ký")
    user = User(email=email, password_hash=hash_password(body.password), full_name=body.full_name)
    db.add(user)
    db.commit()
    return _signed_in(user, response, request)


@router.post("/login", response_model=Token)
def login(body: Login, db: DB, request: Request, response: Response):
    limit(f"login-ip:{client_ip(request)}", 30, 900)
    limit(f"login:{body.email.lower()}", 10, 900)
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email hoặc mật khẩu không đúng")
    if user.disabled_at:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Tài khoản đã bị khoá, liên hệ GrowthPilot")
    if user.totp_secret:  # second step: the 6-digit code, within 5 minutes
        mfa = create_token(str(user.id), minutes=5, purpose="mfa", fp=_fingerprint(user))
        return Token(access_token="", mfa_required=True, mfa_token=mfa)
    return _signed_in(user, response, request)


RESET_MINUTES = 30


def _fingerprint(user: User) -> str:
    return password_fingerprint(user.password_hash)


@router.post("/forgot-password", status_code=202)
def forgot_password(body: ForgotPassword, db: DB, bg: BackgroundTasks, request: Request):
    limit(f"forgot:{client_ip(request)}", 5, 3600)
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
def reset_password(body: ResetPassword, db: DB, request: Request, response: Response):
    limit(f"reset:{client_ip(request)}", 10, 3600)
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
    return _signed_in(user, response, request)


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
        is_platform_admin=is_platform_admin(user),
        mfa_enabled=bool(user.totp_secret),
    )


@router.post("/logout", status_code=204)
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE)


# --- two-factor sign-in (TOTP, any authenticator app) ---


class MfaVerify(BaseModel):
    mfa_token: str = Field(max_length=2000)
    code: str = Field(min_length=6, max_length=8)


class MfaSetup(BaseModel):
    secret: str
    otpauth_url: str


class MfaEnable(BaseModel):
    secret: str = Field(min_length=16, max_length=64)
    code: str = Field(min_length=6, max_length=8)


def _code_ok(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code.strip().replace(" ", ""), valid_window=1)


@router.post("/2fa/verify", response_model=Token)
def mfa_verify(body: MfaVerify, db: DB, request: Request, response: Response):
    limit(f"mfa:{client_ip(request)}", 10, 900)
    bad = HTTPException(status.HTTP_401_UNAUTHORIZED, "Mã xác thực không đúng hoặc đã hết hạn")
    try:
        claims = decode_token(body.mfa_token)
        user = db.get(User, uuid.UUID(claims["sub"])) if claims.get("purpose") == "mfa" else None
    except (jwt.PyJWTError, KeyError, ValueError):
        raise bad from None
    if user is None or claims.get("fp") != _fingerprint(user) or not user.totp_secret:
        raise bad
    if not _code_ok(decrypt_secret(user.totp_secret), body.code):
        raise bad
    return _signed_in(user, response, request)


@router.get("/2fa/setup", response_model=MfaSetup)
def mfa_setup(user: CurrentUser):
    if user.totp_secret:
        raise HTTPException(status.HTTP_409_CONFLICT, "Tài khoản đã bật xác thực hai lớp")
    secret = pyotp.random_base32()
    url = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name="GrowthPilot")
    return MfaSetup(secret=secret, otpauth_url=url)


@router.post("/2fa/enable", status_code=204)
def mfa_enable(body: MfaEnable, user: CurrentUser, db: DB):
    if not _code_ok(body.secret, body.code):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Mã chưa đúng, thử mã mới trong app"
        )
    user.totp_secret = encrypt_secret(body.secret)
    db.commit()


# --- the signed-in user's own account ---


class ProfilePatch(BaseModel):
    full_name: str = Field(max_length=200)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)


@router.patch("/me", status_code=204)
def update_me(body: ProfilePatch, user: CurrentUser, db: DB):
    user.full_name = body.full_name.strip()
    db.commit()


@router.post("/change-password", response_model=Token)
def change_password(
    body: PasswordChange, user: CurrentUser, db: DB, request: Request, response: Response
):
    limit(f"pw-change:{user.id}", 10, 900)
    if not verify_password(body.current_password, user.password_hash):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Mật khẩu hiện tại không đúng")
    user.password_hash = hash_password(body.new_password)  # every other session ends here
    db.commit()
    return _signed_in(user, response, request)
