"""add monthly report automation

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-11

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

dispatch_kind = postgresql.ENUM(
    "initial", "reminder", name="monthlyreportdispatchkind", create_type=False
)


def upgrade() -> None:
    op.add_column(
        "startups",
        sa.Column(
            "monthly_report_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "executives",
        sa.Column(
            "receives_monthly_report",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    dispatch_kind.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "monthly_report_dispatches",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column(
            "startup_id",
            sa.UUID(),
            sa.ForeignKey("startups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "executive_id",
            sa.UUID(),
            sa.ForeignKey("executives.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("recipient_email", sa.String(255), nullable=False),
        sa.Column("month", sa.SmallInteger(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("kind", dispatch_kind, nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "startup_id",
            "executive_id",
            "month",
            "year",
            "kind",
            name="uq_monthly_report_dispatch_recipient_period_kind",
        ),
    )


def downgrade() -> None:
    op.drop_table("monthly_report_dispatches")
    dispatch_kind.drop(op.get_bind(), checkfirst=True)
    op.drop_column("executives", "receives_monthly_report")
    op.drop_column("startups", "monthly_report_enabled")
