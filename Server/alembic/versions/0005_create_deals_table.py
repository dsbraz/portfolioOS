"""create deals table

Revision ID: 0005
Revises: 0004
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "deals",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("empresa", sa.String(255), nullable=False),
        sa.Column("setor", sa.String(255), nullable=True),
        sa.Column("estagio", sa.String(100), nullable=True),
        sa.Column("fundadores", sa.Text(), nullable=True),
        sa.Column(
            "coluna",
            sa.Enum(
                "novo",
                "conversando",
                "analisando",
                "comite",
                "investido",
                "arquivado",
                name="dealcoluna",
            ),
            nullable=False,
            server_default="novo",
        ),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("proximo_passo", sa.Text(), nullable=True),
        sa.Column("responsavel_interno", sa.String(255), nullable=True),
        sa.Column("posicao", sa.Integer(), nullable=False, server_default="0"),
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
    )


def downgrade() -> None:
    op.drop_table("deals")
    op.execute("DROP TYPE IF EXISTS dealcoluna")
