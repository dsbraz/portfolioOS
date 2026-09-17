from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.monthly_indicator.create_monthly_indicator import (
    CreateMonthlyIndicator,
)


@pytest.fixture
def repo():
    mock = AsyncMock()
    mock.update.side_effect = lambda ind: ind
    return mock


@pytest.fixture
def use_case(repo):
    return CreateMonthlyIndicator(repository=repo)


@pytest.fixture
def any_period():
    with patch(
        "app.application.monthly_indicator.create_monthly_indicator.validate_period_not_future"
    ):
        yield


@pytest.mark.asyncio
@pytest.mark.usefixtures("any_period")
async def test_creates_new_indicator(use_case, repo):
    indicator = MagicMock(month=1, year=2025, startup_id="abc")
    repo.get_or_create.return_value = (indicator, True)

    result = await use_case.execute(indicator)

    assert result is indicator
    repo.get_or_create.assert_awaited_once_with(indicator)
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.usefixtures("any_period")
async def test_merges_into_the_stored_indicator(use_case, repo):
    existing = MagicMock(headcount=5, total_revenue=None)
    repo.get_or_create.return_value = (existing, False)
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

    result = await use_case.execute(indicator)

    assert result is existing
    assert existing.headcount == 10
    assert existing.total_revenue == 50000
    repo.update.assert_awaited_once_with(existing)


@pytest.mark.asyncio
async def test_validates_period_not_future(use_case, repo):
    indicator = MagicMock(month=12, year=2099, startup_id="abc")

    with pytest.raises(ValueError, match="futuro"):
        await use_case.execute(indicator)

    repo.get_or_create.assert_not_awaited()
