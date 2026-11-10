"""staff invitations by email

Revision ID: d9a3b5c7e1f0
Revises: c4d8e1f2a7b6
Create Date: 2026-11-10 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.core.db

revision: str = "d9a3b5c7e1f0"
down_revision: str | Sequence[str] | None = "c4d8e1f2a7b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "workspace_invites",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("invited_by", sa.Uuid(), nullable=True),
        sa.Column("expires_at", app.core.db.UTCDateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", app.core.db.UTCDateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", app.core.db.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["invited_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_workspace_invites_email", "workspace_invites", ["email"])
    op.create_index("ix_workspace_invites_workspace_id", "workspace_invites", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_workspace_invites_workspace_id", table_name="workspace_invites")
    op.drop_index("ix_workspace_invites_email", table_name="workspace_invites")
    op.drop_table("workspace_invites")
