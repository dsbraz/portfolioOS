"""The insert that loses the race for a (startup, period).

The use cases check for an existing row before inserting, so going through them
never reaches the unique constraint. These tests drive the repository with the
duplicate the check would have missed. The use cases' recovery from the
resulting `ConflictError` is covered by their unit tests.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.startup import Startup, StartupStatus
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository

PERIOD = {"month": 5, "year": 2026}
OTHER_PERIOD = {"month": 4, "year": 2026}


async def _startup(session: AsyncSession) -> uuid.UUID:
    startup = Startup(
        name="Concurrency Co",
        status=StartupStatus.HEALTHY,
        sector="tech",
        investment_date=date(2026, 1, 15),
    )
    session.add(startup)
    await session.flush()
    return startup.id


@pytest.mark.asyncio
async def test_duplicate_indicator_raises_conflict_and_keeps_earlier_writes(
    session: AsyncSession,
):
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)
    earlier = await repository.create(
        MonthlyIndicator(startup_id=startup_id, **OTHER_PERIOD, headcount=7)
    )
    await repository.create(MonthlyIndicator(startup_id=startup_id, **PERIOD))

    with pytest.raises(ConflictError):
        await repository.create(MonthlyIndicator(startup_id=startup_id, **PERIOD))

    # Only the failed insert is undone: the request's other writes still commit.
    await session.commit()
    assert earlier.headcount == 7
    stored = await session.scalars(
        select(MonthlyIndicator).where(MonthlyIndicator.startup_id == startup_id)
    )
    assert len(stored.all()) == 2


@pytest.mark.asyncio
async def test_duplicate_token_raises_conflict_and_keeps_earlier_writes(
    session: AsyncSession,
):
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)
    earlier = await repository.create_token(
        MonthlyIndicatorToken(startup_id=startup_id, **OTHER_PERIOD)
    )
    await repository.create_token(MonthlyIndicatorToken(startup_id=startup_id, **PERIOD))

    with pytest.raises(ConflictError):
        await repository.create_token(
            MonthlyIndicatorToken(startup_id=startup_id, **PERIOD)
        )

    await session.commit()
    assert earlier.month == OTHER_PERIOD["month"]
    stored = await session.scalars(
        select(MonthlyIndicatorToken).where(
            MonthlyIndicatorToken.startup_id == startup_id
        )
    )
    assert len(stored.all()) == 2
