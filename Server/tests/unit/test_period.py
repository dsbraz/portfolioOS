import pytest

from app.domain.models.period import Period


def test_key_encodes_year_and_month_as_a_sortable_integer():
    assert Period(year=2026, month=7).key == 202607


def test_from_key_decodes_year_and_month():
    assert Period.from_key(202607) == Period(year=2026, month=7)


def test_from_key_round_trips_key():
    period = Period(year=2025, month=12)

    assert Period.from_key(period.key) == period


def test_previous_within_the_same_year():
    assert Period(year=2026, month=5).previous() == Period(year=2026, month=4)


def test_previous_of_january_is_december_of_the_previous_year():
    assert Period(year=2026, month=1).previous() == Period(year=2025, month=12)


def test_ordering_across_the_year_boundary():
    """Dec/2025 must come BEFORE Jan/2026 even though its month is larger."""
    december = Period(year=2025, month=12)
    january = Period(year=2026, month=1)

    assert december < january
    assert max(december, january) == january


def test_is_immutable():
    period = Period(year=2026, month=1)

    with pytest.raises(AttributeError):
        period.month = 2  # type: ignore[misc]


@pytest.mark.parametrize("month", [0, 13])
def test_rejects_month_out_of_range(month):
    with pytest.raises(ValueError, match="Mes deve estar entre 1 e 12"):
        Period(year=2026, month=month)
