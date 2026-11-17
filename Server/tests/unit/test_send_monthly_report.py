import uuid
from unittest.mock import AsyncMock

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
PLAN = MonthlyReportPlan(
    startup_id=uuid.uuid4(),
    startup_name="Payface",
    period=Period(year=2025, month=12),
    kind=DispatchKind.INITIAL,
    form_token=TOKEN,
    recipients=(RECIPIENT,),
)


@pytest.fixture
def sender():
    return AsyncMock()


@pytest.fixture
def use_case(sender):
    return SendMonthlyReport(sender, BASE_URL + "/", "Equipe de Portfólio")


@pytest.mark.asyncio
async def test_sends_the_request_with_the_link_and_signature(use_case, sender):
    assert await use_case.execute(PLAN, RECIPIENT, DispatchKind.INITIAL) is None

    to, subject, body = sender.send.await_args.args
    assert to == "ana@payface.com"
    assert subject == "Payface — indicadores de dezembro/2025"
    assert f"{BASE_URL}/monthly-indicator/{TOKEN}" in body
    assert body.startswith("Olá, Ana.")
    assert body.endswith("Obrigado pela parceria.\nEquipe de Portfólio")


@pytest.mark.asyncio
async def test_the_kind_decided_by_the_claim_picks_the_text(use_case, sender):
    # The plan says reminder, but the claim may have turned it into the request.
    await use_case.execute(PLAN, RECIPIENT, DispatchKind.REMINDER)

    _, subject, body = sender.send.await_args.args
    assert subject == "Lembrete: Payface — indicadores de dezembro/2025"
    assert "Passando para lembrar" in body


@pytest.mark.asyncio
async def test_a_refused_message_returns_the_reason(use_case, sender):
    sender.send.side_effect = EmailDeliveryError("recusado")

    assert await use_case.execute(PLAN, RECIPIENT, DispatchKind.INITIAL) == "recusado"
