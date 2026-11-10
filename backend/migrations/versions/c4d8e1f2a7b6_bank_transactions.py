"""bank transactions from SePay, kept whether or not they matched a workspace

Revision ID: c4d8e1f2a7b6
Revises: b7e2f4c1a9d3
Create Date: 2026-11-10 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.core.db

revision: str = "c4d8e1f2a7b6"
down_revision: str | Sequence[str] | None = "b7e2f4c1a9d3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bank_transactions",
        sa.Column("external_id", sa.String(length=64), nullable=False),
        sa.Column("amount_vnd", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("reference", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", app.core.db.UTCDateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_bank_transactions_status", "bank_transactions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_bank_transactions_status", table_name="bank_transactions")
    op.drop_table("bank_transactions")
