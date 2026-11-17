from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from app.application.startup.record_startup_exit import RecordStartupExit
from app.application.startup.update_startup import UpdateStartup
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


@pytest.fixture
def indicator_repo():
    mock = AsyncMock()
    mock.get_last_reported_period_by_startups.return_value = {}
    return mock


# --- Startup.is_tracked_in ---


@pytest.mark.parametrize("year,month,expected", [
    (2023, 12, False), (2024, 2, False), (2024, 3, True),
    (2026, 2, True), (2026, 3, False), (2026, 4, False),
])
def test_tracking_runs_from_investment_month_until_before_exit(year, month, expected):
    startup = _startup(exited_on=date(2026, 3, 20))
    assert startup.is_tracked_in(Period(year=year, month=month)) is expected


def test_startup_without_exit_stays_tracked_after_investment():
    assert _startup().is_tracked_in(Period(year=2030, month=1))


def test_entry_and_exit_in_same_month_never_count_as_active():
    startup = _startup(exited_on=date(2024, 3, 20))
    assert not startup.is_tracked_in(Period(year=2024, month=3))


def test_the_model_declares_that_date_and_type_travel_together():
    names = {c.name for c in Startup.__table__.constraints}

    assert "ck_startups_exit_complete" in names


# --- Startup.ensure_accepts_indicator ---


def test_a_startup_without_exit_accepts_any_indicator():
    startup = _startup()

    startup.ensure_accepts_indicator(Period(year=2030, month=1), through_link=True)
    startup.ensure_accepts_indicator(Period(year=2030, month=1), through_link=False)


def test_an_exited_startup_takes_manual_indicators_up_to_its_exit_month():
    # The exit month's numbers often arrive after the exit is recorded.
    startup = _startup(exited_on=date(2026, 3, 20))

    startup.ensure_accepts_indicator(Period(year=2026, month=3), through_link=False)
    startup.ensure_accepts_indicator(Period(year=2026, month=1), through_link=False)


def test_an_exited_startup_refuses_manual_indicators_after_its_exit_month():
    startup = _startup(exited_on=date(2026, 3, 20))

    with pytest.raises(ConflictError):
        startup.ensure_accepts_indicator(
            Period(year=2026, month=4), through_link=False
        )


def test_an_exited_startup_refuses_every_link_report():
    startup = _startup(exited_on=date(2026, 3, 20))

    with pytest.raises(ConflictError):
        startup.ensure_accepts_indicator(Period(year=2026, month=2), through_link=True)


# --- RecordStartupExit ---


@pytest.mark.asyncio
async def test_records_the_exit(repo, indicator_repo):
    startup = _startup()

    result = await RecordStartupExit(repo, indicator_repo).execute(
        startup, date(2026, 3, 20), ExitType.SALE, "Comprada pela Big Co"
    )

    assert result.exited_on == date(2026, 3, 20)
    assert result.exit_type == ExitType.SALE
    assert result.exit_notes == "Comprada pela Big Co"
    repo.update.assert_awaited_once_with(startup)


@pytest.mark.asyncio
async def test_blank_notes_are_stored_as_absent(repo, indicator_repo):
    result = await RecordStartupExit(repo, indicator_repo).execute(
        _startup(), date(2026, 3, 20), ExitType.WRITE_OFF, "   "
    )

    assert result.exit_notes is None


@pytest.mark.asyncio
async def test_recording_twice_is_a_conflict(repo, indicator_repo):
    startup = _startup(exited_on=date(2026, 3, 20), exit_type=ExitType.SALE)

    with pytest.raises(ConflictError):
        await RecordStartupExit(repo, indicator_repo).execute(
            startup, date(2026, 4, 1), ExitType.IPO, None
        )
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_date_cannot_be_in_the_future(repo, indicator_repo):
    tomorrow = date.today() + timedelta(days=1)

    with pytest.raises(InvalidInputError):
        await RecordStartupExit(repo, indicator_repo).execute(_startup(), tomorrow, ExitType.SALE, None)
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_date_cannot_precede_the_investment(repo, indicator_repo):
    startup = _startup(investment_date=date(2024, 3, 10))

    with pytest.raises(InvalidInputError):
        await RecordStartupExit(repo, indicator_repo).execute(
            startup, date(2024, 3, 9), ExitType.SALE, None
        )
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_cannot_precede_a_month_already_reported(repo, indicator_repo):
    # Reports after the exit month would silently drop out of the portfolio.
    startup = _startup()
    indicator_repo.get_last_reported_period_by_startups.return_value = {
        startup.id: Period(year=2026, month=5)
    }

    with pytest.raises(InvalidInputError, match="05/2026"):
        await RecordStartupExit(repo, indicator_repo).execute(
            startup, date(2026, 3, 20), ExitType.SALE, None
        )
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_exit_in_the_last_reported_month_is_accepted(repo, indicator_repo):
    startup = _startup()
    indicator_repo.get_last_reported_period_by_startups.return_value = {
        startup.id: Period(year=2026, month=3)
    }

    result = await RecordStartupExit(repo, indicator_repo).execute(
        startup, date(2026, 3, 1), ExitType.SALE, None
    )

    assert result.exited_on == date(2026, 3, 1)


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


# --- UpdateStartup keeps the exit coherent ---


@pytest.mark.asyncio
async def test_investment_date_cannot_move_past_the_exit(repo):
    startup = _startup(exited_on=date(2026, 3, 20), exit_type=ExitType.SALE)

    with pytest.raises(InvalidInputError):
        await UpdateStartup(repo).execute(
            startup, {"investment_date": date(2026, 3, 21)}
        )
    assert startup.investment_date == date(2024, 3, 10)
    repo.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_investment_date_on_the_exit_day_is_accepted(repo):
    startup = _startup(exited_on=date(2026, 3, 20), exit_type=ExitType.SALE)

    result = await UpdateStartup(repo).execute(
        startup, {"investment_date": date(2026, 3, 20)}
    )

    assert result.investment_date == date(2026, 3, 20)
