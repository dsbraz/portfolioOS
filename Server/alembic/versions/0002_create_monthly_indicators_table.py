"""create monthly_indicators table

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monthly_indicators",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "startup_id",
            sa.UUID(),
            sa.ForeignKey("startups.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("mes", sa.SmallInteger(), nullable=False),
        sa.Column("ano", sa.SmallInteger(), nullable=False),
        sa.Column("receita_total", sa.Numeric(15, 2), nullable=True),
        sa.Column("receita_recorrente_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("margem_bruta_pct", sa.Numeric(5, 2), nullable=True),
        sa.Column("saldo_caixa", sa.Numeric(15, 2), nullable=True),
        sa.Column("headcount", sa.Integer(), nullable=True),
        sa.Column("ebitda_burn", sa.Numeric(15, 2), nullable=True),
        sa.Column("conquistas", sa.Text(), nullable=True),
        sa.Column("desafios", sa.Text(), nullable=True),
        sa.Column("comentarios", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("startup_id", "mes", "ano", name="uq_indicator_startup_month_year"),
    )


def downgrade() -> None:
    op.drop_table("monthly_indicators")
