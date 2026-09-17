from sqlalchemy import Integer, SmallInteger

from app.repositories.monthly_indicator_repository import year_month_key_expression


def test_period_comparison_binds_a_32_bit_integer():
    """Regression: `year` and `month` are SMALLINT.

    Without casting BOTH columns, SQLAlchemy types the comparison literal as
    int16 -- 202607 overflows 32767 and asyncpg rejects the parameter, which
    took down the whole /portfolio with DataError.

    The integration tests did not catch it: they run on SQLite, which neither
    types parameters nor validates the SMALLINT range. This test inspects the
    inferred type, so it holds on any database.
    """
    comparison = year_month_key_expression() <= 202607

    assert isinstance(comparison.right.type, Integer)
    # SmallInteger inherits from Integer, so the check above alone would pass.
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
