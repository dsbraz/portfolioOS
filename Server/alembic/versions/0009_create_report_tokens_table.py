"""create report_tokens table

Revision ID: 0009
Revises: 0008
Create Date: 2026-02-18

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "report_tokens",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "token",
            sa.UUID(),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
            unique=True,
        ),
        sa.Column(
            "startup_id",
            sa.UUID(),
            sa.ForeignKey("startups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "startup_id",
            "month",
            "year",
            name="uq_report_token_startup_month_year",
        ),
    )


def downgrade() -> None:
    op.drop_table("report_tokens")
