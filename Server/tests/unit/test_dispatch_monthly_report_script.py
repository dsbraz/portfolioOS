import uuid
from unittest.mock import MagicMock

import pytest

from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
)
from app.config import Settings
from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.models.period import Period
from app.infrastructure.console_email_sender import ConsoleEmailSender
from app.infrastructure.smtp_email_sender import SmtpEmailSender
from scripts.dispatch_monthly_report import build_email_sender, dispatch_all


def _settings(**overrides) -> Settings:
    return Settings(database_url="postgresql+asyncpg://x", secret_key="x", **overrides)


@pytest.mark.parametrize("environment", ["development", "local"])
def test_console_is_allowed_in_local_environments(environment):
    sender = build_email_sender(_settings(environment=environment))
    assert isinstance(sender, ConsoleEmailSender)


@pytest.mark.parametrize("environment", ["production", "prod", "homologacao", ""])
def test_console_is_refused_anywhere_not_local(environment):
    # It records sends that never left, which would hide them from the reminder.
    with pytest.raises(RuntimeError, match="ambiente local"):
        build_email_sender(_settings(environment=environment))


def test_smtp_needs_a_host_and_a_sender():
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        build_email_sender(_settings(email_backend="smtp"))

    sender = build_email_sender(
        _settings(
            email_backend="smtp", smtp_host="smtp.example.com", smtp_sender="a@b.com"
        )
    )
    assert isinstance(sender, SmtpEmailSender)


def _startup(name):
    startup = MagicMock()
    startup.name = name
    startup.id = uuid.uuid4()
    return startup


def _plan_for(startup, *emails):
    return MonthlyReportPlan(
        startup_id=startup.id,
        startup_name=startup.name,
        period=Period(year=2025, month=12),
        kind=DispatchKind.INITIAL,
        form_token=uuid.uuid4(),
        recipients=tuple(MonthlyReportRecipient(uuid.uuid4(), "X", e) for e in emails),
    )


@pytest.mark.asyncio
async def test_an_unexpected_error_does_not_stop_the_startups_after_it():
    broken, other = _startup("Quebrada"), _startup("Outra")
    sent = []

    async def plan_one(startup):
        if startup is broken:
            raise RuntimeError("banco caiu")
        return _plan_for(startup, "a@x.com", "b@x.com")

    async def send_one(plan, recipient):
        if recipient.email == "a@x.com":
            raise ValueError("cabeçalho inválido")
        sent.append(recipient.email)
        return MagicMock(error=None, recipient_email=recipient.email, kind=plan.kind)

    summary = await dispatch_all([broken, other], plan_one, send_one)

    # The broken plan and the broken recipient fail alone; the rest still go.
    assert sent == ["b@x.com"]
    assert (summary.startups, summary.sent, summary.failed) == (2, 1, 2)


@pytest.mark.asyncio
async def test_delivery_failures_and_skips_are_counted_apart():
    startup = _startup("Payface")

    async def plan_one(_):
        return _plan_for(startup, "ok@x.com", "fail@x.com", "done@x.com")

    async def send_one(plan, recipient):
        if recipient.email == "done@x.com":
            return None  # already sent on an earlier run
        error = "recusado" if recipient.email == "fail@x.com" else None
        return MagicMock(error=error, recipient_email=recipient.email, kind=plan.kind)

    summary = await dispatch_all([startup], plan_one, send_one)

    assert (summary.sent, summary.failed) == (1, 1)
