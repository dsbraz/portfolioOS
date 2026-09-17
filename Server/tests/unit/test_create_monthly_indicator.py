from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.monthly_indicator.create_monthly_indicator import (
    _MERGED_FIELDS,
    CreateMonthlyIndicator,
)
from app.domain.exceptions import ConflictError


@pytest.fixture
def repo():
    mock = AsyncMock()
    mock.get_by_startup_and_period.return_value = None
    mock.create.side_effect = lambda ind: ind
    mock.update.side_effect = lambda ind: ind
    return mock


@pytest.fixture
def use_case(repo):
    return CreateMonthlyIndicator(repository=repo)


@pytest.mark.asyncio
async def test_creates_new_indicator(use_case, repo):
    indicator = MagicMock(month=1, year=2025, startup_id="abc")

    with patch(
        "app.application.monthly_indicator.create_monthly_indicator.validate_period_not_future"
    ):
        result = await use_case.execute(indicator)

    assert result is indicator
    repo.create.assert_awaited_once_with(indicator)


@pytest.mark.asyncio
async def test_upserts_existing_indicator(use_case, repo):
    existing = MagicMock(headcount=5, total_revenue=None)
    repo.get_by_startup_and_period.return_value = existing

    indicator = MagicMock(
        month=1,
        year=2025,
        startup_id="abc",
        headcount=10,
        total_revenue=50000,
        recurring_revenue_pct=None,
        gross_margin_pct=None,
        cash_balance=None,
        ebitda_burn=None,
        achievements=None,
        challenges=None,
        comments=None,
    )

    with patch(
        "app.application.monthly_indicator.create_monthly_indicator.validate_period_not_future"
    ):
        result = await use_case.execute(indicator)

    assert result is existing
    assert existing.headcount == 10
    assert existing.total_revenue == 50000
    repo.update.assert_awaited_once_with(existing)
    repo.create.assert_not_awaited()


@pytest.mark.asyncio
async def test_validates_period_not_future(use_case):
    indicator = MagicMock(month=12, year=2099, startup_id="abc")

    with pytest.raises(ValueError, match="futuro"):
        await use_case.execute(indicator)


@pytest.mark.asyncio
async def test_lost_race_merges_onto_the_row_that_won(use_case, repo):
    winner = MagicMock(total_revenue=None, headcount=10)
    # First check sees nothing; after the failed insert, the winner is there.
    repo.get_by_startup_and_period.side_effect = [None, winner]
    repo.create.side_effect = ConflictError("periodo ja existe")

    incoming = MagicMock(
        month=1,
        year=2025,
        startup_id="abc",
        **{**dict.fromkeys(_MERGED_FIELDS), "total_revenue": 1234},
    )

    with patch(
        "app.application.monthly_indicator.create_monthly_indicator.validate_period_not_future"
    ):
        result = await use_case.execute(incoming)

    # Merged onto the winner: our value lands, the winner's survives.
    assert result is winner
    assert winner.total_revenue == 1234
    assert winner.headcount == 10
    repo.update.assert_awaited_once_with(winner)


@pytest.mark.asyncio
async def test_lost_race_with_no_winner_visible_reraises(use_case, repo):
    # The winner is not visible yet (e.g. its transaction has not committed):
    # re-raise so the controller answers 409.
    repo.get_by_startup_and_period.side_effect = [None, None]
    repo.create.side_effect = ConflictError("periodo ja existe")

    incoming = MagicMock(month=1, year=2025, startup_id="abc")

    with patch(
        "app.application.monthly_indicator.create_monthly_indicator.validate_period_not_future"
    ):
        with pytest.raises(ConflictError):
            await use_case.execute(incoming)
