import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.monthly_report.plan_monthly_report import PlanMonthlyReport
from app.domain.models.monthly_report_dispatch import DispatchKind

TOKEN = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _startup():
    startup = MagicMock()
    startup.id = uuid.uuid4()
    startup.name = "Payface"
    return startup


def _executive(name="Ana Souza", email="ana@payface.com", receives=True):
    executive = MagicMock()
    executive.id = uuid.uuid4()
    executive.name = name
    executive.email = email
    executive.receives_monthly_report = receives
    return executive


@pytest.fixture
def executives():
    repo = AsyncMock()
    repo.get_all_by_startup.return_value = ([_executive()], 1)
    return repo


@pytest.fixture
def indicators():
    repo = AsyncMock()
    repo.get_by_startup_and_period.return_value = None
    repo.get_or_create_token.return_value = (MagicMock(token=TOKEN), True)
    return repo


@pytest.fixture
def use_case(executives, indicators):
    return PlanMonthlyReport(executives, indicators)


@pytest.fixture(autouse=True)
def frozen_today():
    with patch("app.application.monthly_report.plan_monthly_report.date") as fake:
        fake.today.return_value = date(2026, 1, 10)
        yield


@pytest.mark.asyncio
async def test_plans_the_previous_month_link_for_the_marked_executives(
    use_case, indicators
):
    startup = _startup()

    plan = await use_case.execute(startup, DispatchKind.INITIAL)

    # January rolls back to December of the previous year.
    token = indicators.get_or_create_token.await_args.args[0]
    assert (token.startup_id, token.month, token.year) == (startup.id, 12, 2025)
    assert (plan.period.month, plan.period.year) == (12, 2025)
    assert plan.form_token == TOKEN
    assert plan.startup_name == "Payface"
    assert [r.email for r in plan.recipients] == ["ana@payface.com"]


@pytest.mark.asyncio
async def test_skips_executives_not_marked_or_without_email(
    use_case, executives, indicators
):
    executives.get_all_by_startup.return_value = (
        [_executive(receives=False), _executive(email=None), _executive(email="  ")],
        3,
    )

    assert await use_case.execute(_startup(), DispatchKind.INITIAL) is None
    # No recipient, no link: generating one is a write nobody asked for.
    indicators.get_or_create_token.assert_not_awaited()


@pytest.mark.parametrize("kind", list(DispatchKind))
@pytest.mark.asyncio
async def test_skips_a_period_already_reported(use_case, indicators, kind):
    # Who is missing comes from the platform: a startup that already reported
    # the month gets neither the request nor the reminder.
    indicators.get_by_startup_and_period.return_value = MagicMock()

    assert await use_case.execute(_startup(), kind) is None
    indicators.get_or_create_token.assert_not_awaited()


@pytest.mark.asyncio
async def test_one_e_mail_per_inbox_with_a_normalised_address(use_case, executives):
    # Founder and CFO share contato@: the inbox gets one request, not two.
    executives.get_all_by_startup.return_value = (
        [
            _executive(name="Ana", email=" Contato@Payface.com "),
            _executive(name="Bruno", email="contato@payface.com"),
            _executive(name="Carla", email="carla@payface.com"),
        ],
        3,
    )

    plan = await use_case.execute(_startup(), DispatchKind.INITIAL)

    assert [(r.name, r.email) for r in plan.recipients] == [
        ("Ana", "contato@payface.com"),
        ("Carla", "carla@payface.com"),
    ]
