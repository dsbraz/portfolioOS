"""enforce username constraints

Revision ID: 0015
Revises: 0014
Create Date: 2026-03-04

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_users_username_no_space",
        "users",
        "username NOT LIKE '% %'",
    )
    op.create_index(
        "ux_users_username_lower",
        "users",
        [sa.text("lower(username)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ux_users_username_lower", table_name="users")
    op.drop_constraint(
        "ck_users_username_no_space",
        "users",
        type_="check",
    )
