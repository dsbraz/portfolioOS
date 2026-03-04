import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.monthly_indicator.create_monthly_indicator_token import (
    CreateMonthlyIndicatorToken,
)


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

    result = await use_case.execute(startup_id, month=2, year=2026)

    assert result.startup_id == startup_id
    assert result.month == 2
    assert result.year == 2026
    repo.get_token_by_startup_and_period.assert_awaited_once_with(startup_id, 2, 2026)
    repo.create_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_existing_token_if_already_exists(use_case, repo):
    existing = MagicMock()
    repo.get_token_by_startup_and_period.return_value = existing
    startup_id = uuid.uuid4()

    result = await use_case.execute(startup_id, month=2, year=2026)

    assert result is existing
    repo.create_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_raises_error_when_period_is_in_future(use_case, repo):
    startup_id = uuid.uuid4()

    with pytest.raises(ValueError, match="nao pode ser no futuro"):
        await use_case.execute(startup_id, month=1, year=9999)

    repo.get_token_by_startup_and_period.assert_not_awaited()
    repo.create_token.assert_not_awaited()
