"""create startups table

Revision ID: 0001
Revises:
Create Date: 2026-02-17

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

startup_status = postgresql.ENUM(
    "saudavel", "atencao", "critico", name="startupstatus", create_type=False
)


def upgrade() -> None:
    startup_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "startups",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("nome", sa.String(255), nullable=False),
        sa.Column("site", sa.String(512), nullable=True),
        sa.Column("logo_url", sa.String(512), nullable=True),
        sa.Column(
            "status",
            startup_status,
            nullable=False,
            server_default="saudavel",
        ),
        sa.Column("setor", sa.String(255), nullable=False),
        sa.Column("data_investimento", sa.Date(), nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
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
    op.drop_table("startups")
    startup_status.drop(op.get_bind(), checkfirst=True)
