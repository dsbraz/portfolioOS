import uuid
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.domain.models.board_meeting import BoardMeeting
from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.startup import Startup, StartupStatus
from scripts.seed_demo import (
    DEMO_MALICIOUS_INSTRUCTION,
    DEMO_NEXT_STEP,
    DEMO_STARTUP_ID,
    DEMO_STARTUP_NAME,
    ensure_development_environment,
    seed_demo,
)


@pytest.mark.parametrize(
    "environment",
    [
        "prod",
        "production",
        " PRODUCTION ",
        "prd",
        "live",
        "staging",
        "qa",
        "test",
        "dev",
        "not-production",
        "",
    ],
)
def test_demo_seed_rejects_environments_outside_the_local_allowlist(environment):
    with pytest.raises(RuntimeError, match="ENVIRONMENT=development"):
        ensure_development_environment(environment)


@pytest.mark.parametrize("environment", ["development", "local", " LOCAL "])
def test_demo_seed_accepts_only_local_development_environments(environment):
    ensure_development_environment(environment)


@pytest.mark.asyncio
async def test_seed_demo_creates_the_reference_scenario(session):
    await seed_demo(session)

    startup = await session.get(Startup, DEMO_STARTUP_ID)
    assert startup is not None
    assert startup.name == DEMO_STARTUP_NAME
    assert startup.status == StartupStatus.WARNING

    indicators = list(
        (
            await session.execute(
                select(MonthlyIndicator)
                .where(MonthlyIndicator.startup_id == DEMO_STARTUP_ID)
                .order_by(MonthlyIndicator.year, MonthlyIndicator.month)
            )
        )
        .scalars()
        .all()
    )

    assert [(item.year, item.month) for item in indicators] == [
        (2026, 5),
        (2026, 6),
        (2026, 7),
    ]
    assert [item.total_revenue for item in indicators] == [
        Decimal("150000.00"),
        Decimal("135000.00"),
        Decimal("108000.00"),
    ]
    assert all(
        item.achievements is None and item.challenges is None and item.comments is None
        for item in indicators
    )

    meetings = list(
        (
            await session.execute(
                select(BoardMeeting)
                .where(BoardMeeting.startup_id == DEMO_STARTUP_ID)
                .order_by(BoardMeeting.meeting_date)
            )
        )
        .scalars()
        .all()
    )

    assert [item.meeting_date for item in meetings] == [
        date(2026, 6, 12),
        date(2026, 7, 10),
    ]
    assert [item.next_steps for item in meetings] == [
        DEMO_NEXT_STEP,
        DEMO_NEXT_STEP,
    ]
    assert "mês excelente" in meetings[-1].summary.lower()
    assert DEMO_MALICIOUS_INSTRUCTION in meetings[-1].attention_points


@pytest.mark.asyncio
async def test_seed_demo_is_idempotent_and_restores_owned_records(session):
    await seed_demo(session)

    startup = await session.get(Startup, DEMO_STARTUP_ID)
    startup.name = "Changed name"
    latest_indicator = (
        await session.execute(
            select(MonthlyIndicator).where(
                MonthlyIndicator.startup_id == DEMO_STARTUP_ID,
                MonthlyIndicator.month == 7,
                MonthlyIndicator.year == 2026,
            )
        )
    ).scalar_one()
    latest_indicator.total_revenue = Decimal("999999.00")
    latest_indicator.month = 9
    latest_indicator.year = 2025
    session.add(
        MonthlyIndicator(
            id=uuid.UUID("bd1a0bb2-cea3-4ddf-a576-0243b147e458"),
            startup_id=DEMO_STARTUP_ID,
            month=8,
            year=2026,
        )
    )
    session.add(
        BoardMeeting(
            id=uuid.UUID("f803045d-e7fd-45ef-b66c-76dd88e19244"),
            startup_id=DEMO_STARTUP_ID,
            meeting_date=date(2026, 8, 8),
            summary="Record created by the manual skill verification.",
        )
    )
    await session.flush()

    await seed_demo(session)

    assert startup.name == DEMO_STARTUP_NAME
    assert latest_indicator.total_revenue == Decimal("108000.00")
    assert (latest_indicator.year, latest_indicator.month) == (2026, 7)

    startup_count = await session.scalar(
        select(func.count()).select_from(Startup).where(Startup.id == DEMO_STARTUP_ID)
    )
    indicator_count = await session.scalar(
        select(func.count())
        .select_from(MonthlyIndicator)
        .where(MonthlyIndicator.startup_id == DEMO_STARTUP_ID)
    )
    meeting_count = await session.scalar(
        select(func.count())
        .select_from(BoardMeeting)
        .where(BoardMeeting.startup_id == DEMO_STARTUP_ID)
    )

    assert startup_count == 1
    assert indicator_count == 3
    assert meeting_count == 2


@pytest.mark.asyncio
async def test_seed_demo_does_not_change_records_owned_by_another_startup(session):
    other_startup_id = uuid.UUID("bd958559-865a-492d-902c-cd4d66688cf8")
    other_indicator_id = uuid.UUID("29c6247a-dd63-4885-ad3d-aa20ec74ad67")
    other_meeting_id = uuid.UUID("1dfe8049-b5d7-428d-92ef-c908711d15c1")
    session.add(
        Startup(
            id=other_startup_id,
            name="Unrelated startup",
            status=StartupStatus.HEALTHY,
            sector="Fintech",
            investment_date=date(2025, 1, 10),
        )
    )
    session.add(
        MonthlyIndicator(
            id=other_indicator_id,
            startup_id=other_startup_id,
            month=8,
            year=2026,
            total_revenue=Decimal("42000.00"),
        )
    )
    session.add(
        BoardMeeting(
            id=other_meeting_id,
            startup_id=other_startup_id,
            meeting_date=date(2026, 8, 8),
            summary="Unrelated meeting",
        )
    )
    await session.flush()

    await seed_demo(session)
    await seed_demo(session)

    other_startup = await session.get(Startup, other_startup_id)
    other_indicator = await session.get(MonthlyIndicator, other_indicator_id)
    other_meeting = await session.get(BoardMeeting, other_meeting_id)

    assert other_startup is not None
    assert other_startup.name == "Unrelated startup"
    assert other_indicator is not None
    assert other_indicator.startup_id == other_startup_id
    assert other_indicator.total_revenue == Decimal("42000.00")
    assert other_meeting is not None
    assert other_meeting.startup_id == other_startup_id
    assert other_meeting.summary == "Unrelated meeting"
