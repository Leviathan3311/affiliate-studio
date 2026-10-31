import uuid
from dataclasses import dataclass
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import decode_token
from app.models import AuditLog, User, Workspace, WorkspaceMember

DB = Annotated[Session, Depends(get_db)]
_bearer = HTTPBearer(auto_error=False)


def current_user(
    db: DB, cred: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)]
) -> User:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Missing token")
    try:
        user_id = uuid.UUID(decode_token(cred.credentials)["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token") from None
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid token")
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


def workspace_ctx(db: DB, user: CurrentUser, x_workspace_id: Annotated[uuid.UUID, Header()]) -> Ctx:
    row = db.execute(
        select(Workspace, WorkspaceMember.role)
        .join(WorkspaceMember, WorkspaceMember.workspace_id == Workspace.id)
        .where(Workspace.id == x_workspace_id, WorkspaceMember.user_id == user.id)
    ).first()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Workspace not found")
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
Marketing = Annotated[Ctx, Depends(require("admin", "marketing"))]
Sales = Annotated[Ctx, Depends(require("admin", "sales", "branch_manager"))]
