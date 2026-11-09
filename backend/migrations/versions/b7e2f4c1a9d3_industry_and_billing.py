"""business type on brands; trial/paid period and payments for billing

Revision ID: b7e2f4c1a9d3
Revises: a3c19e7d52b1
Create Date: 2026-11-09 17:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.core.db

revision: str = "b7e2f4c1a9d3"
down_revision: str | Sequence[str] | None = "a3c19e7d52b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("brands", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("industry", sa.String(length=100), nullable=False, server_default="")
        )
    with op.batch_alter_table("workspaces", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("paid_until", app.core.db.UTCDateTime(timezone=True), nullable=True)
        )
    op.create_table(
        "payments",
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("months", sa.Integer(), nullable=False),
        sa.Column("amount_vnd", sa.Integer(), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.Column("created_by", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", app.core.db.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payments_workspace_id", "payments", ["workspace_id"])


def downgrade() -> None:
    op.drop_index("ix_payments_workspace_id", table_name="payments")
    op.drop_table("payments")
    with op.batch_alter_table("workspaces", schema=None) as batch_op:
        batch_op.drop_column("paid_until")
    with op.batch_alter_table("brands", schema=None) as batch_op:
        batch_op.drop_column("industry")
