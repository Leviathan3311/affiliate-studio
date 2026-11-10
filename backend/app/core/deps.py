import uuid
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.plan import is_active
from app.core.security import decode_token, password_fingerprint
from app.models import AuditLog, User, Workspace, WorkspaceMember

DB = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


SESSION_COOKIE = "gp_session"


def current_user(
    request: Request, db: DB, cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> User:
    # The web app uses the httpOnly cookie; scripts and the media worker send a bearer token.
    token = cred.credentials if cred else request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    try:
        claims = decode_token(token)
        if "purpose" in claims:  # OAuth state and reset links are not sessions
            raise KeyError("purpose")
        user_id = uuid.UUID(claims["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from None
    user = db.get(User, user_id)
    if user is None or claims.get("pv") != password_fingerprint(user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")  # e.g. password changed
    return user


CurrentUser = Annotated[User, Depends(current_user)]


@dataclass
class Ctx:
    db: Session
    user: User
    workspace: Workspace
    role: str

    @property
    def ws_id(self) -> uuid.UUID:
        return self.workspace.id

    def audit(self, action: str, target_type: str = "", target_id="", **meta) -> None:
        self.db.add(
            AuditLog(
                workspace_id=self.ws_id,
                actor_user_id=self.user.id,
                action=action,
                target_type=target_type,
                target_id=str(target_id),
                meta=meta,
            )
        )

    def get(self, model, obj_id: uuid.UUID):
        """Fetch a workspace-scoped row or 404 — the single tenant-isolation choke point."""
        obj = self.db.get(model, obj_id)
        if obj is None or obj.workspace_id != self.ws_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"{model.__name__} not found")
        return obj


# Reachable after the trial or paid period ends: see the plan, pay, or delete the workspace.
OPEN_WHEN_EXPIRED = {"/api/v1/billing", "/api/v1/workspace"}


def workspace_ctx(
    request: Request, db: DB, user: CurrentUser, x_workspace_id: Annotated[uuid.UUID, Header()]
) -> Ctx:
    row = db.execute(
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(Workspace.id == x_workspace_id, WorkspaceMember.user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
    if request.url.path not in OPEN_WHEN_EXPIRED and not is_active(row[0]):
        raise HTTPException(
            status.HTTP_402_PAYMENT_REQUIRED,
            "Gói của cửa hàng đã hết hạn, vui lòng gia hạn để dùng tiếp",
        )
    return Ctx(db=db, user=user, workspace=row[0], role=row[1])


def require(*roles: str):
    """RBAC (MOD-01). Owner always passes."""

    def dep(ctx: Annotated[Ctx, Depends(workspace_ctx)]) -> Ctx:
        if ctx.role != "owner" and ctx.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Insufficient role")
        return ctx

    return dep


AnyMember = Annotated[Ctx, Depends(workspace_ctx)]
Admin = Annotated[Ctx, Depends(require("admin"))]
Owner = Annotated[Ctx, Depends(require())]
Marketing = Annotated[Ctx, Depends(require("admin", "marketing"))]
Sales = Annotated[Ctx, Depends(require("admin", "sales", "branch_manager"))]
