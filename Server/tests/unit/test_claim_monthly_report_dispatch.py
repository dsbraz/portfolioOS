import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.application.monthly_report.claim_monthly_report_dispatch import (
    ClaimMonthlyReportDispatch,
)
from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
)
from app.domain.models.monthly_report_dispatch import (
    DispatchKind,
    MonthlyReportDispatch,
)
from app.domain.models.period import Period

NOW = datetime(2026, 1, 20, 12, 0, tzinfo=UTC)
DAY_10 = datetime(2026, 1, 10, 12, 0, tzinfo=UTC)
RECIPIENT = MonthlyReportRecipient(uuid.uuid4(), "Ana Souza", "ana@payface.com")


def _plan(kind=DispatchKind.INITIAL):
    return MonthlyReportPlan(
        startup_id=uuid.uuid4(),
        startup_name="Payface",
        period=Period(year=2025, month=12),
        kind=kind,
        form_token=uuid.uuid4(),
        recipients=(RECIPIENT,),
    )


def _stored(*, sent_at=None, error=None, attempted_at=DAY_10):
    return MonthlyReportDispatch(
        id=uuid.uuid4(),
        recipient_email=RECIPIENT.email,
        kind=DispatchKind.INITIAL,
        attempted_at=attempted_at,
        sent_at=sent_at,
        error=error,
    )


@pytest.fixture(autouse=True)
def frozen_now():
    with patch(
        "app.application.monthly_report.claim_monthly_report_dispatch.datetime"
    ) as fake:
        fake.now.return_value = NOW
        yield


@pytest.fixture
def dispatches():
    repo = AsyncMock()
    repo.get_or_create.side_effect = lambda dispatch: (dispatch, True)
    repo.update.side_effect = lambda dispatch: dispatch
    repo.find.return_value = _stored(sent_at=DAY_10)  # the request went out on day 10
    return repo


@pytest.fixture
def use_case(dispatches):
    return ClaimMonthlyReportDispatch(dispatches)


@pytest.mark.asyncio
async def test_claims_a_new_send_before_it_leaves(use_case):
    dispatch = await use_case.execute(_plan(), RECIPIENT)

    assert (dispatch.month, dispatch.year, dispatch.kind) == (12, 2025, DispatchKind.INITIAL)
    assert dispatch.recipient_email == "ana@payface.com"
    assert dispatch.attempted_at == NOW
    # Neither delivered nor failed until the outcome is recorded.
    assert dispatch.sent_at is None and dispatch.error is None


@pytest.mark.parametrize(
    "stored",
    [_stored(sent_at=DAY_10), _stored()],
    ids=["delivered", "unconfirmed"],
)
@pytest.mark.asyncio
async def test_never_resends_a_delivered_or_unconfirmed_send(
    use_case, dispatches, stored
):
    # Unconfirmed may have left: a duplicate in the inbox is worse than a gap
    # the operator can see in the history.
    dispatches.get_or_create.side_effect = None
    dispatches.get_or_create.return_value = (stored, False)

    assert await use_case.execute(_plan(), RECIPIENT) is None
    dispatches.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_retries_a_failed_send_as_a_fresh_attempt(use_case, dispatches):
    failed = _stored(error="timeout")
    dispatches.get_or_create.side_effect = None
    dispatches.get_or_create.return_value = (failed, False)

    dispatch = await use_case.execute(_plan(), RECIPIENT)

    assert dispatch is failed
    assert failed.error is None
    assert failed.attempted_at == NOW
    dispatches.update.assert_awaited_once_with(failed)


@pytest.mark.asyncio
async def test_reminder_follows_a_request_delivered_on_an_earlier_day(
    use_case, dispatches
):
    dispatch = await use_case.execute(_plan(DispatchKind.REMINDER), RECIPIENT)

    assert dispatch.kind is DispatchKind.REMINDER
    # Looked up by address: the inbox is what got the request.
    startup_id, email, *_ = dispatches.find.await_args.args
    assert email == "ana@payface.com"


@pytest.mark.parametrize(
    "initial",
    [None, _stored(error="SMTPRecipientsRefused")],
    ids=["never-sent-to-this-address", "failed"],
)
@pytest.mark.asyncio
async def test_reminder_without_a_delivered_request_sends_the_request(
    use_case, dispatches, initial
):
    # Also covers a changed address: the new inbox has no request on record.
    dispatches.find.return_value = initial

    dispatch = await use_case.execute(_plan(DispatchKind.REMINDER), RECIPIENT)

    assert dispatch.kind is DispatchKind.INITIAL


@pytest.mark.parametrize(
    "initial",
    [
        _stored(sent_at=NOW, attempted_at=NOW),
        _stored(sent_at=NOW, attempted_at=datetime(2026, 1, 20, 0, 5, tzinfo=UTC)),
    ],
    ids=["minutes-ago", "earlier-today"],
)
@pytest.mark.asyncio
async def test_rerun_of_the_reminder_does_not_remind_a_request_sent_today(
    use_case, dispatches, initial
):
    # The first reminder run sent the request as the replacement; a rerun must
    # not follow it with "we still have not received it" minutes later.
    dispatches.find.return_value = initial

    assert await use_case.execute(_plan(DispatchKind.REMINDER), RECIPIENT) is None
    dispatches.get_or_create.assert_not_awaited()


@pytest.mark.asyncio
async def test_reminder_after_an_unconfirmed_request_still_goes(use_case, dispatches):
    # It carries the same link: the safe way to make sure the request arrived.
    dispatches.find.return_value = _stored()

    dispatch = await use_case.execute(_plan(DispatchKind.REMINDER), RECIPIENT)

    assert dispatch.kind is DispatchKind.REMINDER
