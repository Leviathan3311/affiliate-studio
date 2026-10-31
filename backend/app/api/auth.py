import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import select

from app.deps import DB, CurrentUser
from app.models import User, Workspace, WorkspaceMember
from app.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


class Register(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(default="", max_length=200)


class Login(BaseModel):
    email: EmailStr
    password: str


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
