"""create user_invites table

Revision ID: 0014
Revises: 0013
Create Date: 2026-03-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "user_invites",
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
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_user_invites_email", "user_invites", ["email"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_user_invites_email", table_name="user_invites")
    op.drop_table("user_invites")
