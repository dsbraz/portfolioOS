import uuid
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.portfolio.get_portfolio_summary import GetPortfolioSummary
from app.domain.models.startup import StartupStatus


@pytest.fixture
def startup_repo():
    return AsyncMock()


@pytest.fixture
def indicator_repo():
    return AsyncMock()


@pytest.fixture
def meeting_repo():
    return AsyncMock()


@pytest.fixture
def use_case(startup_repo, indicator_repo, meeting_repo):
    return GetPortfolioSummary(
        startup_repo=startup_repo,
        indicator_repo=indicator_repo,
        meeting_repo=meeting_repo,
    )


def _make_startup(status=StartupStatus.HEALTHY):
    s = MagicMock()
    s.id = uuid.uuid4()
    s.status = status
    return s


@pytest.mark.asyncio
async def test_empty_portfolio(use_case, startup_repo, indicator_repo, meeting_repo):
    startup_repo.get_all.return_value = ([], 0)

    result = await use_case.execute()

    assert result.total_startups == 0
    assert result.revenue == Decimal("0")
    assert result.revenue_variation_pct is None
    assert result.revenue_variation_direction == "neutral"
    assert result.health.healthy == 0
    indicator_repo.get_by_startups_and_period.assert_not_awaited()


@pytest.mark.asyncio
async def test_health_distribution(
    use_case, startup_repo, indicator_repo, meeting_repo
):
    startups = [
        _make_startup(StartupStatus.HEALTHY),
        _make_startup(StartupStatus.HEALTHY),
        _make_startup(StartupStatus.WARNING),
        _make_startup(StartupStatus.CRITICAL),
    ]
    startup_repo.get_all.return_value = (startups, 4)
    indicator_repo.get_by_startups_and_period.return_value = {}
    meeting_repo.get_startup_ids_with_recent_meetings.return_value = set()

    result = await use_case.execute()

    assert result.total_startups == 4
    assert result.health.healthy == 2
    assert result.health.warning == 1
    assert result.health.critical == 1


@pytest.mark.asyncio
async def test_revenue_aggregation(
    use_case, startup_repo, indicator_repo, meeting_repo
):
    s1 = _make_startup()
    s2 = _make_startup()
    startup_repo.get_all.return_value = ([s1, s2], 2)

    ind1 = MagicMock(
        total_revenue=Decimal("100000"),
        cash_balance=None,
        ebitda_burn=None,
        headcount=None,
        month=1,
        year=2026,
    )
    ind2 = MagicMock(
        total_revenue=Decimal("50000"),
        cash_balance=None,
        ebitda_burn=None,
        headcount=None,
        month=1,
        year=2026,
    )
    indicator_repo.get_by_startups_and_period.side_effect = [
        {s1.id: ind1, s2.id: ind2},
        {},
    ]
    meeting_repo.get_startup_ids_with_recent_meetings.return_value = set()

    result = await use_case.execute(month=1, year=2026)

    assert result.revenue == Decimal("150000")
    assert result.revenue_variation_pct is None
    assert result.revenue_variation_direction == "neutral"
    assert len(result.startups) == 2
    assert indicator_repo.get_by_startups_and_period.await_count == 2
    meeting_repo.get_startup_ids_with_recent_meetings.assert_awaited_once_with(
        [s1.id, s2.id], 90, date(2026, 1, 31)
    )


@pytest.mark.asyncio
async def test_revenue_variation_should_be_positive(
    use_case, startup_repo, indicator_repo, meeting_repo
):
    s1 = _make_startup()
    startup_repo.get_all.return_value = ([s1], 1)

    current = MagicMock(
        total_revenue=Decimal("120000"),
        cash_balance=None,
        ebitda_burn=None,
        headcount=None,
    )
    previous = MagicMock(total_revenue=Decimal("100000"))
    indicator_repo.get_by_startups_and_period.side_effect = [
        {s1.id: current},
        {s1.id: previous},
    ]
    meeting_repo.get_startup_ids_with_recent_meetings.return_value = set()

    result = await use_case.execute(month=2, year=2026)

    assert result.revenue_variation_pct == 20.0
    assert result.revenue_variation_direction == "up"


@pytest.mark.asyncio
async def test_revenue_variation_should_be_negative(
    use_case, startup_repo, indicator_repo, meeting_repo
):
    s1 = _make_startup()
    startup_repo.get_all.return_value = ([s1], 1)

    current = MagicMock(
        total_revenue=Decimal("90000"),
        cash_balance=None,
        ebitda_burn=None,
        headcount=None,
    )
    previous = MagicMock(total_revenue=Decimal("100000"))
    indicator_repo.get_by_startups_and_period.side_effect = [
        {s1.id: current},
        {s1.id: previous},
    ]
    meeting_repo.get_startup_ids_with_recent_meetings.return_value = set()

    result = await use_case.execute(month=2, year=2026)

    assert result.revenue_variation_pct == -10.0
    assert result.revenue_variation_direction == "down"


@pytest.mark.asyncio
async def test_should_raise_when_only_month_is_provided(use_case):
    with pytest.raises(ValueError, match="Mes e ano devem ser informados juntos"):
        await use_case.execute(month=1)


@pytest.mark.asyncio
async def test_should_raise_when_period_is_in_the_future(use_case):
    future = date.today()
    month = 1 if future.month == 12 else future.month + 1
    year = future.year + 1 if future.month == 12 else future.year

    with pytest.raises(ValueError, match="nao pode ser no futuro"):
        await use_case.execute(month=month, year=year)
