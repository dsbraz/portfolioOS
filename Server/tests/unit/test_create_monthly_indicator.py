from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.monthly_indicator.create_monthly_indicator import (
    CreateMonthlyIndicator,
)


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


# --- Losing the insert race (the branch the integration test cannot reach) ---
#
# The integration test pre-inserts the winner, so the guard finds it and the
# `except ConflictError` branch never runs. Only a repo that returns "nothing
# there" and THEN raises on create reproduces the true interleaving.


@pytest.mark.asyncio
async def test_lost_race_merges_onto_the_row_that_won(repo):
    from app.domain.exceptions import ConflictError

    winner = MagicMock(total_revenue=None, headcount=10)
    # First check sees nothing; after the failed insert, the winner is there.
    repo.get_by_startup_and_period.side_effect = [None, winner]
    repo.create.side_effect = ConflictError("periodo ja existe")

    incoming = MagicMock(month=1, year=2025, startup_id="abc")
    incoming.total_revenue = 1234
    incoming.headcount = None
    for field in (
        "recurring_revenue_pct", "gross_margin_pct", "cash_balance",
        "ebitda_burn", "achievements", "challenges", "comments",
    ):
        setattr(incoming, field, None)

    with patch(
        "app.application.monthly_indicator.create_monthly_indicator.validate_period_not_future"
    ):
        result = await CreateMonthlyIndicator(repo).execute(incoming)

    # Merged onto the winner: our value lands, the winner's survives.
    assert result is winner
    assert winner.total_revenue == 1234
    assert winner.headcount == 10
    repo.update.assert_awaited_once_with(winner)


@pytest.mark.asyncio
async def test_lost_race_with_no_winner_visible_reraises(repo):
    from app.domain.exceptions import ConflictError

    # Pathological: insert conflicts but the row is not visible either (e.g. the
    # winner's transaction has not committed). Swallowing this would return
    # nothing; re-raising lets the controller answer 409 honestly.
    repo.get_by_startup_and_period.side_effect = [None, None]
    repo.create.side_effect = ConflictError("periodo ja existe")

    incoming = MagicMock(month=1, year=2025, startup_id="abc")

    with patch(
        "app.application.monthly_indicator.create_monthly_indicator.validate_period_not_future"
    ):
        with pytest.raises(ConflictError):
            await CreateMonthlyIndicator(repo).execute(incoming)
