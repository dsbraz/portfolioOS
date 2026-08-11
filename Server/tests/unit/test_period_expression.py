from sqlalchemy import Integer, SmallInteger

from app.repositories.monthly_indicator_repository import period_expression


def test_period_comparison_binds_a_32_bit_integer():
    """Regressao: `year` e `month` sao SMALLINT.

    Sem converter as DUAS colunas, o SQLAlchemy tipa o literal da comparacao
    como int16 -- 202607 estoura 32767 e o asyncpg recusa o parametro, o que
    derrubava /portfolio inteiro com DataError.

    Os testes de integracao nao pegaram: rodam em SQLite, que nao tipa
    parametro nem valida a faixa de SMALLINT. Este teste olha o tipo inferido,
    e por isso vale em qualquer banco.
    """
    comparison = period_expression() <= 202607

    assert isinstance(comparison.right.type, Integer)
    # SmallInteger herda de Integer, entao a checagem acima sozinha passaria.
    assert not isinstance(comparison.right.type, SmallInteger)


def test_period_expression_orders_across_the_year_boundary():
    """Dez/2025 (202512) tem de vir ANTES de Jan/2026 (202601)."""
    assert 2025 * 100 + 12 < 2026 * 100 + 1
