import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.application.monthly_report.record_monthly_report_outcome import (
    RecordMonthlyReportOutcome,
)
from app.domain.models.monthly_report_dispatch import (
    DispatchKind,
    MonthlyReportDispatch,
)

CLAIMED_AT = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)
ACCEPTED_AT = datetime(2026, 1, 10, 12, 0, 4, tzinfo=UTC)


@pytest.fixture(autouse=True)
def frozen_now():
    with patch(
        "app.application.monthly_report.record_monthly_report_outcome.datetime"
    ) as fake:
        fake.now.return_value = ACCEPTED_AT
        yield


@pytest.fixture
def claimed():
    return MonthlyReportDispatch(
        id=uuid.uuid4(),
        kind=DispatchKind.INITIAL,
        recipient_email="ana@payface.com",
        attempted_at=CLAIMED_AT,
    )


@pytest.fixture
def dispatches(claimed):
    repo = AsyncMock()
    repo.get_by_id.return_value = claimed
    repo.update.side_effect = lambda dispatch: dispatch
    return repo


@pytest.mark.asyncio
async def test_a_delivery_is_dated_when_the_relay_accepted_it(dispatches, claimed):
    dispatch = await RecordMonthlyReportOutcome(dispatches).execute(claimed.id, None)

    assert dispatch.delivered and not dispatch.failed
    assert dispatch.sent_at == ACCEPTED_AT
    dispatches.update.assert_awaited_once_with(claimed)


@pytest.mark.asyncio
async def test_a_failure_keeps_the_reason_and_no_delivery_date(dispatches, claimed):
    dispatch = await RecordMonthlyReportOutcome(dispatches).execute(
        claimed.id, "recusado"
    )

    assert dispatch.failed and not dispatch.delivered
    assert dispatch.error == "recusado"


@pytest.mark.asyncio
async def test_a_send_that_vanished_is_ignored(dispatches):
    # The startup was deleted mid-run: the cascade took its history with it.
    dispatches.get_by_id.return_value = None

    assert await RecordMonthlyReportOutcome(dispatches).execute(uuid.uuid4(), None) is None
    dispatches.update.assert_not_awaited()
