"""platform admins can lock an account

Revision ID: f3a7b9d1c5e2
Revises: e2f6a8c0b4d1
Create Date: 2026-11-10 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

import app.core.db

revision: str = "f3a7b9d1c5e2"
down_revision: str | Sequence[str] | None = "e2f6a8c0b4d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("disabled_at", app.core.db.UTCDateTime(timezone=True), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("disabled_at")
