from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from app.application.startup.record_startup_exit import RecordStartupExit
from app.application.startup.undo_startup_exit import UndoStartupExit
from app.domain.exceptions import ConflictError, InvalidInputError
from app.domain.models.period import Period
from app.domain.models.startup import ExitType, Startup


def _startup(**overrides) -> Startup:
    fields = {
        "name": "Acme",
        "sector": "tech",
        "investment_date": date(2024, 3, 10),
    }
    fields.update(overrides)
    return Startup(**fields)


@pytest.fixture
def repo():
    mock = AsyncMock()
    mock.update.side_effect = lambda s: s
    return mock


# --- Startup.is_tracked_in ---


def test_a_startup_without_exit_is_tracked_in_any_period():
    assert _startup().is_tracked_in(Period(year=2030, month=1))


def test_a_startup_is_still_tracked_in_the_month_it_exited():
    startup = _startup(exited_on=date(2026, 3, 20))

    assert startup.is_tracked_in(Period(year=2026, month=3))
    assert startup.is_tracked_in(Period(year=2026, month=2))


def test_a_startup_is_not_tracked_after_the_month_it_exited():
    startup = _startup(exited_on=date(2026, 3, 20))

    assert not startup.is_tracked_in(Period(year=2026, month=4))
    assert not startup.is_tracked_in(Period(year=2027, month=1))


# --- RecordStartupExit ---


@pytest.mark.asyncio
async def test_records_the_exit(repo):
    startup = _startup()

    result = await RecordStartupExit(repo).execute(
        startup, date(2026, 3, 20), ExitType.SALE, "Comprada pela Big Co"
    )

    assert result.exited_on == date(2026, 3, 20)
    assert result.exit_type == ExitType.SALE
    assert result.exit_notes == "Comprada pela Big Co"
    repo.update.assert_awaited_once_with(startup)


@pytest.mark.asyncio
async def test_blank_notes_are_stored_as_absent(repo):
    result = await RecordStartupExit(repo).execute(
        _startup(), date(2026, 3, 20), ExitType.WRITE_OFF, "   "
    )

    assert result.exit_notes is None


@pytest.mark.asyncio
async def test_recording_twice_is_a_conflict(repo):
    startup = _startup(exited_on=date(2026, 3, 20), exit_type=ExitType.SALE)

    with pytest.raises(ConflictError):
        await RecordStartupExit(repo).execute(
            startup, date(2026, 4, 1), ExitType.IPO, None
        )
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_date_cannot_be_in_the_future(repo):
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(InvalidInputError):
        await RecordStartupExit(repo).execute(_startup(), tomorrow, ExitType.SALE, None)
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_date_cannot_precede_the_investment(repo):
    startup = _startup(investment_date=date(2024, 3, 10))

    with pytest.raises(InvalidInputError):
        await RecordStartupExit(repo).execute(
            startup, date(2024, 3, 9), ExitType.SALE, None
        )
    repo.update.assert_not_awaited()


# --- UndoStartupExit ---


@pytest.mark.asyncio
async def test_undo_clears_the_exit(repo):
    startup = _startup(
        exited_on=date(2026, 3, 20), exit_type=ExitType.SALE, exit_notes="x"
    )

    result = await UndoStartupExit(repo).execute(startup)

    assert result.exited_on is None
    assert result.exit_type is None
    assert result.exit_notes is None
    repo.update.assert_awaited_once_with(startup)


@pytest.mark.asyncio
async def test_undo_without_an_exit_is_a_conflict(repo):
    with pytest.raises(ConflictError):
        await UndoStartupExit(repo).execute(_startup())
    repo.update.assert_not_awaited()
