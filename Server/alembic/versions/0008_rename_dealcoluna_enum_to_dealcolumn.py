"""rename dealcoluna enum to dealcolumn

Revision ID: 0008
Revises: 0007
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE dealcoluna RENAME TO dealcolumn")


def downgrade() -> None:
    op.execute("ALTER TYPE dealcolumn RENAME TO dealcoluna")
