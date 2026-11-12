import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
)
from app.application.monthly_report.send_monthly_report import SendMonthlyReport
from app.domain.email_sender import EmailDeliveryError
from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.models.period import Period

BASE_URL = "https://portfolio.example.com"
TOKEN = uuid.UUID("00000000-0000-0000-0000-000000000001")
RECIPIENT = MonthlyReportRecipient(uuid.uuid4(), "Ana Souza", "ana@payface.com")


def _plan(kind=DispatchKind.INITIAL):
    return MonthlyReportPlan(
        startup_id=uuid.uuid4(),
        startup_name="Payface",
        period=Period(year=2025, month=12),
        kind=kind,
        form_token=TOKEN,
        recipients=(RECIPIENT,),
    )


@pytest.fixture
def dispatches():
    repo = AsyncMock()
    repo.get_or_create.side_effect = lambda dispatch: (dispatch, True)
    repo.update.side_effect = lambda dispatch: dispatch
    repo.find.return_value = MagicMock(error=None)  # the initial went out
    return repo


@pytest.fixture
def sender():
    return AsyncMock()


@pytest.fixture
def use_case(dispatches, sender):
    return SendMonthlyReport(dispatches, sender, BASE_URL, "Equipe de Portfólio")


@pytest.mark.asyncio
async def test_sends_the_initial_e_mail_and_records_it(use_case, sender):
    dispatch = await use_case.execute(_plan(), RECIPIENT)

    to, subject, body = sender.send.await_args.args
    assert to == "ana@payface.com"
    assert subject == "Payface — indicadores de dezembro/2025"
    assert f"{BASE_URL}/monthly-indicator/{TOKEN}" in body
    assert body.startswith("Olá, Ana.")
    assert body.endswith("Obrigado pela parceria.\nEquipe de Portfólio")
    assert (dispatch.month, dispatch.year, dispatch.kind) == (12, 2025, DispatchKind.INITIAL)
    assert dispatch.error is None


@pytest.mark.asyncio
async def test_reminder_uses_the_reminder_text_after_an_initial_that_went_out(
    use_case, sender
):
    dispatch = await use_case.execute(_plan(DispatchKind.REMINDER), RECIPIENT)

    _, subject, body = sender.send.await_args.args
    assert subject == "Lembrete: Payface — indicadores de dezembro/2025"
    assert "Passando para lembrar" in body
    assert dispatch.kind is DispatchKind.REMINDER


@pytest.mark.parametrize(
    "initial", [None, MagicMock(error="SMTPRecipientsRefused")], ids=["never", "failed"]
)
@pytest.mark.asyncio
async def test_reminder_without_a_delivered_initial_sends_the_initial(
    use_case, dispatches, sender, initial
):
    # "We still have not received it" would refer to a message they never saw.
    dispatches.find.return_value = initial

    dispatch = await use_case.execute(_plan(DispatchKind.REMINDER), RECIPIENT)

    _, subject, body = sender.send.await_args.args
    assert not subject.startswith("Lembrete")
    assert "Já está disponível" in body
    assert dispatch.kind is DispatchKind.INITIAL


@pytest.mark.asyncio
async def test_does_not_resend_what_was_already_sent(use_case, dispatches, sender):
    dispatches.get_or_create.side_effect = None
    dispatches.get_or_create.return_value = (MagicMock(error=None), False)

    assert await use_case.execute(_plan(), RECIPIENT) is None
    sender.send.assert_not_awaited()


@pytest.mark.asyncio
async def test_retries_a_failed_send_to_the_current_address(
    use_case, dispatches, sender
):
    failed = MagicMock(error="timeout", recipient_email="old@payface.com")
    dispatches.get_or_create.side_effect = None
    dispatches.get_or_create.return_value = (failed, False)

    dispatch = await use_case.execute(_plan(), RECIPIENT)

    assert sender.send.await_args.args[0] == "ana@payface.com"
    assert dispatch is failed
    assert failed.error is None
    assert failed.recipient_email == "ana@payface.com"
    dispatches.update.assert_awaited_once_with(failed)


@pytest.mark.asyncio
async def test_delivery_failure_is_recorded(use_case, dispatches, sender):
    sender.send.side_effect = EmailDeliveryError("recusado")

    dispatch = await use_case.execute(_plan(), RECIPIENT)

    assert dispatch.error == "recusado"
    dispatches.update.assert_awaited_once()
