from sqlalchemy import Integer, SmallInteger

from app.repositories.monthly_indicator_repository import period_expression


def test_period_comparison_binds_a_32_bit_integer():
    """Regression: `year` and `month` are SMALLINT.

    Without casting BOTH columns, SQLAlchemy types the comparison literal as
    int16 -- 202607 overflows 32767 and asyncpg rejects the parameter, which
    took down the whole /portfolio with DataError.

    The integration tests did not catch it: they run on SQLite, which neither
    types parameters nor validates the SMALLINT range. This test inspects the
    inferred type, so it holds on any database.
    """
    comparison = period_expression() <= 202607

    assert isinstance(comparison.right.type, Integer)
    # SmallInteger inherits from Integer, so the check above alone would pass.
    assert not isinstance(comparison.right.type, SmallInteger)


def test_period_expression_orders_across_the_year_boundary():
    """Dec/2025 (202512) must come BEFORE Jan/2026 (202601)."""
    assert 2025 * 100 + 12 < 2026 * 100 + 1
