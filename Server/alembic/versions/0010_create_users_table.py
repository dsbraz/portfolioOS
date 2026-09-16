"""create users table

Revision ID: 0010
Revises: 0009
Create Date: 2026-02-19

"""

from typing import Sequence, Union

from alembic import op
from passlib.context import CryptContext
import sqlalchemy as sa


revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    users_table = op.create_table(
        "users",
        sa.Column(
            "id",
            sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "username",
            sa.String(150),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "email",
            sa.String(255),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "hashed_password",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
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

    op.bulk_insert(
        users_table,
        [
            {
                "username": "admin",
                "email": "admin@portfolio.local",
                "hashed_password": pwd_context.hash("admin123"),
            }
        ],
    )


def downgrade() -> None:
    op.drop_table("users")
