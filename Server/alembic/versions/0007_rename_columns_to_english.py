"""rename columns from Portuguese to English

Revision ID: 0007
Revises: 0006
Create Date: 2026-02-18

"""
from typing import Sequence, Union

from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

STARTUPS_RENAMES = [
    ("nome", "name"),
    ("setor", "sector"),
    ("data_investimento", "investment_date"),
    ("observacao", "notes"),
]

MONTHLY_INDICATORS_RENAMES = [
    ("mes", "month"),
    ("ano", "year"),
    ("receita_total", "total_revenue"),
    ("receita_recorrente_pct", "recurring_revenue_pct"),
    ("margem_bruta_pct", "gross_margin_pct"),
    ("saldo_caixa", "cash_balance"),
    ("conquistas", "achievements"),
    ("desafios", "challenges"),
    ("comentarios", "comments"),
]

BOARD_MEETINGS_RENAMES = [
    ("data", "meeting_date"),
    ("participantes", "participants"),
    ("resumo", "summary"),
    ("pontos_atencao", "attention_points"),
    ("proximos_passos", "next_steps"),
]

EXECUTIVES_RENAMES = [
    ("nome", "name"),
    ("cargo", "role"),
    ("telefone", "phone"),
]

DEALS_RENAMES = [
    ("empresa", "company"),
    ("setor", "sector"),
    ("estagio", "stage"),
    ("fundadores", "founders"),
    ("coluna", "column"),
    ("notas", "notes"),
    ("proximo_passo", "next_step"),
    ("responsavel_interno", "internal_owner"),
    ("posicao", "position"),
]


def _rename_columns(table: str, renames: list[tuple[str, str]]) -> None:
    for old, new in renames:
        op.alter_column(table, old, new_column_name=new)


def _revert_columns(table: str, renames: list[tuple[str, str]]) -> None:
    for old, new in renames:
        op.alter_column(table, new, new_column_name=old)


def upgrade() -> None:
    _rename_columns("startups", STARTUPS_RENAMES)
    _rename_columns("monthly_indicators", MONTHLY_INDICATORS_RENAMES)
    _rename_columns("board_meetings", BOARD_MEETINGS_RENAMES)
    _rename_columns("executives", EXECUTIVES_RENAMES)
    _rename_columns("deals", DEALS_RENAMES)

    op.drop_constraint("uq_indicator_startup_month_year", "monthly_indicators", type_="unique")
    op.create_unique_constraint(
        "uq_indicator_startup_month_year", "monthly_indicators", ["startup_id", "month", "year"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_indicator_startup_month_year", "monthly_indicators", type_="unique")
    op.create_unique_constraint(
        "uq_indicator_startup_month_year", "monthly_indicators", ["startup_id", "mes", "ano"]
    )

    _revert_columns("deals", DEALS_RENAMES)
    _revert_columns("executives", EXECUTIVES_RENAMES)
    _revert_columns("board_meetings", BOARD_MEETINGS_RENAMES)
    _revert_columns("monthly_indicators", MONTHLY_INDICATORS_RENAMES)
    _revert_columns("startups", STARTUPS_RENAMES)
