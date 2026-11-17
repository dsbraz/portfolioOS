import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.monthly_indicator.create_monthly_indicator_token import (
    CreateMonthlyIndicatorToken,
)
from app.domain.exceptions import ConflictError
from app.domain.models.startup import ExitType, Startup


def _startup(**overrides) -> Startup:
    fields = {
        "id": uuid.uuid4(),
        "name": "Acme",
        "sector": "tech",
        "investment_date": date(2024, 3, 10),
    }
    fields.update(overrides)
    return Startup(**fields)


@pytest.fixture
def repo():
    return AsyncMock()


@pytest.fixture
def use_case(repo):
    return CreateMonthlyIndicatorToken(repository=repo)


@pytest.mark.asyncio
async def test_creates_new_token(use_case, repo):
    repo.get_or_create_token.side_effect = lambda token: (token, True)
    startup = _startup()

    result = await use_case.execute(startup, month=2, year=2026)

    assert result.startup_id == startup.id
    assert result.month == 2
    assert result.year == 2026
    repo.get_or_create_token.assert_awaited_once()


@pytest.mark.asyncio
async def test_returns_the_stored_token_for_the_period(use_case, repo):
    existing = MagicMock()
    repo.get_or_create_token.return_value = (existing, False)

    result = await use_case.execute(_startup(), month=2, year=2026)

    assert result is existing


@pytest.mark.asyncio
async def test_raises_error_when_period_is_in_future(use_case, repo):
    with pytest.raises(ValueError, match="nao pode ser no futuro"):
        await use_case.execute(_startup(), month=1, year=9999)

    repo.get_or_create_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_an_exited_startup_gets_no_link(use_case, repo):
    startup = _startup(exited_on=date(2026, 3, 20), exit_type=ExitType.SALE)

    with pytest.raises(ConflictError):
        await use_case.execute(startup, month=2, year=2026)

    repo.get_or_create_token.assert_not_awaited()
