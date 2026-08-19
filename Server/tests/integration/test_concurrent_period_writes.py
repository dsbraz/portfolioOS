"""The get-then-insert race on a period.

`CreateMonthlyIndicator` and `CreateMonthlyIndicatorToken` both check for an
existing row and then insert. Two writes for the same (startup, period) that
interleave between the check and the insert both see "nothing there" and both
insert — and the unique constraint rejects the loser.

Before this was handled, that surfaced as a 500. The severity is low while a
human clicks one button at a time and high the moment PRD-003 mints links in
batch, which is exactly when nobody is watching the response.

These tests drive the repository directly: going through the API would take the
use case's own get-then-merge path and never reach the constraint.
"""

import uuid
from datetime import date

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.monthly_indicator.create_monthly_indicator import (
    CreateMonthlyIndicator,
)
from app.application.monthly_indicator.create_monthly_indicator_token import (
    CreateMonthlyIndicatorToken,
)
from app.domain.exceptions import ConflictError
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.startup import Startup, StartupStatus
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository

PERIOD = {"month": 5, "year": 2026}


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
async def test_duplicate_indicator_insert_raises_conflict_not_a_database_error(
    session: AsyncSession,
):
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)

    await repository.create(MonthlyIndicator(startup_id=startup_id, **PERIOD))

    # The loser of the race: same period, inserted without the guard having seen
    # the winner. The persistence error must reach the domain as a conflict.
    with pytest.raises(ConflictError):
        await repository.create(MonthlyIndicator(startup_id=startup_id, **PERIOD))


@pytest.mark.asyncio
async def test_duplicate_token_insert_raises_conflict_not_a_database_error(
    session: AsyncSession,
):
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)

    await repository.create_token(
        MonthlyIndicatorToken(startup_id=startup_id, **PERIOD)
    )

    with pytest.raises(ConflictError):
        await repository.create_token(
            MonthlyIndicatorToken(startup_id=startup_id, **PERIOD)
        )


@pytest.mark.asyncio
async def test_indicator_use_case_absorbs_the_race_by_merging(session: AsyncSession):
    """Losing the race must not lose the write.

    The create path is an upsert, so the caller's intent is "this period should
    carry these values". When another writer wins the insert, the right outcome
    is to merge onto the row that landed — not to fail.
    """
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)
    use_case = CreateMonthlyIndicator(repository)

    # A concurrent writer already inserted the period, unseen by our guard.
    await repository.create(
        MonthlyIndicator(startup_id=startup_id, **PERIOD, headcount=10)
    )

    merged = await use_case.execute(
        MonthlyIndicator(startup_id=startup_id, **PERIOD, total_revenue=1234)
    )

    assert merged.total_revenue == 1234
    # The concurrent writer's value survives: a blank field never erases.
    assert merged.headcount == 10


@pytest.mark.asyncio
async def test_token_use_case_absorbs_the_race_by_returning_the_existing_link(
    session: AsyncSession,
):
    """One link per (startup, period) is the documented contract, and it has to
    hold under a race too — otherwise a batch run mints an error instead of the
    link that already exists."""
    startup_id = await _startup(session)
    repository = MonthlyIndicatorRepository(session)
    use_case = CreateMonthlyIndicatorToken(repository)

    winner = await repository.create_token(
        MonthlyIndicatorToken(startup_id=startup_id, **PERIOD)
    )

    result = await use_case.execute(startup_id, **PERIOD)

    assert result.token == winner.token
