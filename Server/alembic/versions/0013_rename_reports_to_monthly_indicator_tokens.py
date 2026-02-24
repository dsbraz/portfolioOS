"""rename reports to monthly_indicator_tokens

Revision ID: 0013
Revises: 0012
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op


revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("reports", "monthly_indicator_tokens")
    op.execute(
        "ALTER INDEX uq_report_startup_month_year "
        "RENAME TO uq_monthly_indicator_token_startup_month_year"
    )


def downgrade() -> None:
    op.execute(
        "ALTER INDEX uq_monthly_indicator_token_startup_month_year "
        "RENAME TO uq_report_startup_month_year"
    )
    op.rename_table("monthly_indicator_tokens", "reports")
