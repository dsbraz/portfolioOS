import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.monthly_indicator.create_monthly_indicator_token import (
    CreateMonthlyIndicatorToken,
    _previous_month,
)


def test_previous_month_regular():
    with patch(
        "app.application.monthly_indicator.create_monthly_indicator_token.date"
    ) as mock_date:
        mock_date.today.return_value = date(2026, 3, 15)
        assert _previous_month() == (2, 2026)


def test_previous_month_january_wraps_to_december():
    with patch(
        "app.application.monthly_indicator.create_monthly_indicator_token.date"
    ) as mock_date:
        mock_date.today.return_value = date(2026, 1, 10)
        assert _previous_month() == (12, 2025)


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def use_case(repo):
    return CreateMonthlyIndicatorToken(repository=repo)


@pytest.mark.asyncio
async def test_creates_new_token(use_case, repo):
    repo.get_token_by_startup_and_period.return_value = None
    repo.create_token.side_effect = lambda t: t
    startup_id = uuid.uuid4()

    result = await use_case.execute(startup_id)

    assert result.startup_id == startup_id
    repo.create_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_existing_token_if_already_exists(use_case, repo):
    existing = MagicMock()
    repo.get_token_by_startup_and_period.return_value = existing
    startup_id = uuid.uuid4()

    result = await use_case.execute(startup_id)

    assert result is existing
    repo.create_token.assert_not_awaited()
