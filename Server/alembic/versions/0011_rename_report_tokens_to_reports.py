"""rename report_tokens to reports

Revision ID: 0011
Revises: 0010
Create Date: 2026-02-24

"""

from typing import Sequence, Union

from alembic import op


revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.rename_table("report_tokens", "reports")
    op.execute(
        "ALTER INDEX uq_report_token_startup_month_year "
        "RENAME TO uq_report_startup_month_year"
    )


def downgrade() -> None:
    op.execute(
        "ALTER INDEX uq_report_startup_month_year "
        "RENAME TO uq_report_token_startup_month_year"
    )
    op.rename_table("reports", "report_tokens")
