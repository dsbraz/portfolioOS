"""Get-or-create on a (startup, period) when another request races for it.

The repository recovers from the lost insert, so these tests drive it directly
and simulate the race by making the lookup miss the row that is already there.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.startup import Startup, StartupStatus
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository

PERIOD = {"month": 5, "year": 2026}
OTHER_PERIOD = {"month": 4, "year": 2026}

RECORDS = pytest.mark.parametrize(
    ("model", "finder", "get_or_create"),
    [
        (MonthlyIndicator, "get_by_startup_and_period", "get_or_create"),
        (MonthlyIndicatorToken, "get_token_by_startup_and_period", "get_or_create_token"),
    ],
)


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


async def _count(session: AsyncSession, model: type, startup_id: uuid.UUID) -> int:
    return await session.scalar(
        select(func.count()).select_from(model).where(model.startup_id == startup_id)
    )


def _lookup_misses(repository, finder: str, monkeypatch, times: int | None) -> None:
    """Make the lookup see nothing `times` times (always when None)."""
    real = getattr(repository, finder)
    calls = 0

    async def fake(*args):
        nonlocal calls
        calls += 1
        if times is None or calls <= times:
            return None
        return await real(*args)

    monkeypatch.setattr(repository, finder, fake)


@pytest.mark.asyncio
@RECORDS
async def test_free_period_is_inserted(session, model, finder, get_or_create):
    startup_id = await _startup(session)
    record = model(startup_id=startup_id, **PERIOD)

    result, created = await getattr(MonthlyIndicatorRepository(session), get_or_create)(
        record
    )

    assert created is True
    assert result is record
    assert await _count(session, model, startup_id) == 1


@pytest.mark.asyncio
@RECORDS
async def test_taken_period_returns_the_stored_row(session, model, finder, get_or_create):
    startup_id = await _startup(session)
    upsert = getattr(MonthlyIndicatorRepository(session), get_or_create)
    first, _ = await upsert(model(startup_id=startup_id, **PERIOD))

    result, created = await upsert(model(startup_id=startup_id, **PERIOD))

    assert created is False
    assert result.id == first.id
    assert await _count(session, model, startup_id) == 1


@pytest.mark.asyncio
@RECORDS
async def test_lost_race_returns_the_winner_and_keeps_earlier_writes(
    session, monkeypatch, model, finder, get_or_create
):
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)
    upsert = getattr(repository, get_or_create)
    await upsert(model(startup_id=startup_id, **OTHER_PERIOD))
    winner, _ = await upsert(model(startup_id=startup_id, **PERIOD))
    _lookup_misses(repository, finder, monkeypatch, times=1)

    result, created = await upsert(model(startup_id=startup_id, **PERIOD))

    assert created is False
    assert result.id == winner.id
    # Only the lost insert is undone: the request's other writes still commit.
    await session.commit()
    assert await _count(session, model, startup_id) == 2


@pytest.mark.asyncio
@RECORDS
async def test_lost_race_without_a_visible_winner_raises_conflict(
    session, monkeypatch, model, finder, get_or_create
):
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)
    upsert = getattr(repository, get_or_create)
    await upsert(model(startup_id=startup_id, **OTHER_PERIOD))
    await upsert(model(startup_id=startup_id, **PERIOD))
    _lookup_misses(repository, finder, monkeypatch, times=None)

    with pytest.raises(ConflictError):
        await upsert(model(startup_id=startup_id, **PERIOD))

    await session.commit()
    assert await _count(session, model, startup_id) == 2


@pytest.mark.asyncio
@RECORDS
async def test_other_integrity_errors_are_not_reported_as_a_taken_period(
    session, model, finder, get_or_create
):
    # A foreign key that points nowhere: the violation is real, and it is not a
    # taken period. The repository must let it through instead of reading every
    # IntegrityError as "someone else got here first".
    upsert = getattr(MonthlyIndicatorRepository(session), get_or_create)

    with pytest.raises(IntegrityError):
        await upsert(model(startup_id=uuid.uuid4(), **PERIOD))
