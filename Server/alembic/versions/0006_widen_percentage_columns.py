"""widen percentage columns from Numeric(5,2) to Numeric(7,2)

Revision ID: 0006
Revises: 0005
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "monthly_indicators",
        "receita_recorrente_pct",
        type_=sa.Numeric(7, 2),
        existing_type=sa.Numeric(5, 2),
    )
    op.alter_column(
        "monthly_indicators",
        "margem_bruta_pct",
        type_=sa.Numeric(7, 2),
        existing_type=sa.Numeric(5, 2),
    )


def downgrade() -> None:
    op.alter_column(
        "monthly_indicators",
        "receita_recorrente_pct",
        type_=sa.Numeric(5, 2),
        existing_type=sa.Numeric(7, 2),
    )
    op.alter_column(
        "monthly_indicators",
        "margem_bruta_pct",
        type_=sa.Numeric(5, 2),
        existing_type=sa.Numeric(7, 2),
    )
