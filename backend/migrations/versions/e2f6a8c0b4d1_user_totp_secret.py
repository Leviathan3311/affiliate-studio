"""two-factor sign-in: encrypted TOTP secret on users

Revision ID: e2f6a8c0b4d1
Revises: d9a3b5c7e1f0
Create Date: 2026-11-10 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e2f6a8c0b4d1"
down_revision: str | Sequence[str] | None = "d9a3b5c7e1f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("totp_secret", sa.Text(), nullable=False, server_default=""))


def downgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("totp_secret")
