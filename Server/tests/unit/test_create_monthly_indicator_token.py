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
    repo.get_or_create_token.side_effect = lambda token: (token, True)
    startup_id = uuid.uuid4()

    result = await use_case.execute(startup_id, month=2, year=2026)

    assert result.startup_id == startup_id
    assert result.month == 2
    assert result.year == 2026
    repo.get_or_create_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_the_stored_token_for_the_period(use_case, repo):
    existing = MagicMock()
    repo.get_or_create_token.return_value = (existing, False)

    result = await use_case.execute(uuid.uuid4(), month=2, year=2026)

    assert result is existing


@pytest.mark.asyncio
async def test_raises_error_when_period_is_in_future(use_case, repo):
    with pytest.raises(ValueError, match="nao pode ser no futuro"):
        await use_case.execute(uuid.uuid4(), month=1, year=9999)

    repo.get_or_create_token.assert_not_awaited()
