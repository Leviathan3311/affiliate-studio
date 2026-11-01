"""chat scope: separate script and media assistants

Revision ID: a3c19e7d52b1
Revises: d6bf23cb05f3
Create Date: 2026-11-02 00:10:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a3c19e7d52b1"
down_revision: str | Sequence[str] | None = "d6bf23cb05f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("project_chat_messages", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("scope", sa.String(length=16), nullable=False, server_default="script")
        )


def downgrade() -> None:
    with op.batch_alter_table("project_chat_messages", schema=None) as batch_op:
        batch_op.drop_column("scope")
