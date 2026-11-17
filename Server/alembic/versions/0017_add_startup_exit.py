"""add exit fields to startups

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-17

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

exit_type = postgresql.ENUM(
    "venda", "ipo", "recompra", "baixa", name="exit_type", create_type=False
)


def upgrade() -> None:
    exit_type.create(op.get_bind(), checkfirst=True)
    op.add_column("startups", sa.Column("exited_on", sa.Date(), nullable=True))
    op.add_column("startups", sa.Column("exit_type", exit_type, nullable=True))
    op.add_column("startups", sa.Column("exit_notes", sa.Text(), nullable=True))
    # Date and type travel together: one without the other is not an exit.
    op.create_check_constraint(
        "ck_startups_exit_complete",
        "startups",
        "(exited_on IS NULL) = (exit_type IS NULL)",
    )


def downgrade() -> None:
    op.drop_constraint("ck_startups_exit_complete", "startups", type_="check")
    op.drop_column("startups", "exit_notes")
    op.drop_column("startups", "exit_type")
    op.drop_column("startups", "exited_on")
    exit_type.drop(op.get_bind(), checkfirst=True)
