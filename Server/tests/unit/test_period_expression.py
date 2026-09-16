from sqlalchemy import Integer, SmallInteger

from app.repositories.monthly_indicator_repository import year_month_key_expression


def test_period_comparison_binds_a_32_bit_integer():
    """Regressao: `year` e `month` sao SMALLINT.

    Sem converter as DUAS colunas, o SQLAlchemy tipa o literal da comparacao
    como int16 -- 202607 estoura 32767 e o asyncpg recusa o parametro, o que
    derrubava /portfolio inteiro com DataError.

    Os testes de integracao nao pegaram: rodam em SQLite, que nao tipa
    parametro nem valida a faixa de SMALLINT. Este teste olha o tipo inferido,
    e por isso vale em qualquer banco.
    """
    comparison = year_month_key_expression() <= 202607

    assert isinstance(comparison.right.type, Integer)
    # SmallInteger herda de Integer, entao a checagem acima sozinha passaria.
    assert not isinstance(comparison.right.type, SmallInteger)


def test_year_month_key_expression_compiles_to_year_times_100_plus_month():
    """Must match `Period.key`, which decodes the query result."""
    sql = str(
        year_month_key_expression().compile(compile_kwargs={"literal_binds": True})
    )

    assert sql == (
        "CAST(monthly_indicators.year AS INTEGER) * 100"
        " + CAST(monthly_indicators.month AS INTEGER)"
    )
