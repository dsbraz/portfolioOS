"""rename deal stage and column fields

Revision ID: 0012
Revises: 0011
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op


revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column("deals", "stage", new_column_name="funding_round")
    op.alter_column("deals", "column", new_column_name="stage")
    op.execute("ALTER TYPE dealcolumn RENAME TO dealstage")


def downgrade() -> None:
    op.execute("ALTER TYPE dealstage RENAME TO dealcolumn")
    op.alter_column("deals", "stage", new_column_name="column")
    op.alter_column("deals", "funding_round", new_column_name="stage")
