import uuid
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
    assert result.health.healthy == 0
    indicator_repo.get_latest_by_startups.assert_not_awaited()


@pytest.mark.asyncio
async def test_health_distribution(use_case, startup_repo, indicator_repo, meeting_repo):
    startups = [
        _make_startup(StartupStatus.HEALTHY),
        _make_startup(StartupStatus.HEALTHY),
        _make_startup(StartupStatus.WARNING),
        _make_startup(StartupStatus.CRITICAL),
    ]
    startup_repo.get_all.return_value = (startups, 4)
    indicator_repo.get_latest_by_startups.return_value = {}
    meeting_repo.get_startup_ids_with_recent_meetings.return_value = set()

    result = await use_case.execute()

    assert result.total_startups == 4
    assert result.health.healthy == 2
    assert result.health.warning == 1
    assert result.health.critical == 1


@pytest.mark.asyncio
async def test_revenue_aggregation(use_case, startup_repo, indicator_repo, meeting_repo):
    s1 = _make_startup()
    s2 = _make_startup()
    startup_repo.get_all.return_value = ([s1, s2], 2)

    ind1 = MagicMock(total_revenue=Decimal("100000"), cash_balance=None, ebitda_burn=None, headcount=None, month=1, year=2026)
    ind2 = MagicMock(total_revenue=Decimal("50000"), cash_balance=None, ebitda_burn=None, headcount=None, month=1, year=2026)
    indicator_repo.get_latest_by_startups.return_value = {s1.id: ind1, s2.id: ind2}
    meeting_repo.get_startup_ids_with_recent_meetings.return_value = set()

    result = await use_case.execute()

    assert result.revenue == Decimal("150000")
    assert len(result.startups) == 2
