"""Monthly job: e-mail the reporting link of the month that just closed.

Run by a Cloud Run Job on a Cloud Scheduler trigger (see DEPLOY.md):

    python -m scripts.dispatch_monthly_report --kind initial    # day 10
    python -m scripts.dispatch_monthly_report --kind reminder   # day 20

The period is the month before today. A manual rerun after the month turned
names the one it means, or it would start the next month instead:

    python -m scripts.dispatch_monthly_report --kind reminder --period 2026-10

Each startup is planned in its own transaction. Each recipient takes three
steps: the send is claimed and committed, the e-mail leaves outside any
transaction, and the outcome is recorded in another. A failure can stop
neither the recipients nor the startups after it.

A rerun retries the sends that failed and skips the delivered ones. A send
whose outcome could not be recorded stays unconfirmed: it is reported as
NÃO CONFIRMADO, shown as such in the history, and never resent by the job —
a duplicate in an executive's inbox is worse than a gap the operator can see.

`EMAIL_BACKEND` defaults to `console`, which prints instead of sending and is
accepted only in local environments: it records the sends, and anywhere real it
would mark as delivered mail that never left.
"""

import argparse
import asyncio
import traceback
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.application.monthly_report.claim_monthly_report_dispatch import (
    ClaimMonthlyReportDispatch,
)
from app.application.monthly_report.list_startups_for_monthly_report import (
    ListStartupsForMonthlyReport,
)
from app.application.monthly_report.plan_monthly_report import PlanMonthlyReport
from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
    MonthlyReportSkip,
)
from app.application.monthly_report.record_monthly_report_outcome import (
    RecordMonthlyReportOutcome,
)
from app.application.monthly_report.send_monthly_report import SendMonthlyReport
from app.config import LOCAL_ENVIRONMENTS, Settings, settings
from app.domain.email_sender import EmailSender
from app.domain.exceptions import InvalidInputError
from app.domain.models.monthly_report_dispatch import (
    DispatchKind,
    MonthlyReportDispatch,
)
from app.domain.models.period import Period
from app.domain.models.startup import Startup
from app.domain.validators import validate_period_closed
from app.infrastructure.console_email_sender import ConsoleEmailSender
from app.infrastructure.smtp_email_sender import SmtpEmailSender
from app.repositories.executive_repository import ExecutiveRepository
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.monthly_report_dispatch_repository import (
    MonthlyReportDispatchRepository,
)
from app.repositories.startup_repository import StartupRepository


def build_email_sender(config: Settings) -> EmailSender:
    backend = config.email_backend.strip().lower()
    if backend == "console":
        if config.environment.strip().lower() not in LOCAL_ENVIRONMENTS:
            raise RuntimeError(
                "EMAIL_BACKEND=console só é permitido em ambiente local "
                f"(ENVIRONMENT={config.environment!r}); use EMAIL_BACKEND=smtp"
            )
        return ConsoleEmailSender()
    if backend != "smtp":
        raise RuntimeError(f"EMAIL_BACKEND desconhecido: {config.email_backend!r}")
    if not config.smtp_host or not config.smtp_sender:
        raise RuntimeError("EMAIL_BACKEND=smtp exige SMTP_HOST e SMTP_SENDER")
    return SmtpEmailSender(
        host=config.smtp_host,
        port=config.smtp_port,
        sender=config.smtp_sender,
        username=config.smtp_username,
        password=config.smtp_password,
        starttls=config.smtp_starttls,
    )


@dataclass
class DispatchSummary:
    startups: int = 0
    sent: int = 0
    failed: int = 0
    without_recipients: int = 0


PlanOne = Callable[[Startup], Awaitable[MonthlyReportPlan | MonthlyReportSkip]]
SendOne = Callable[
    [MonthlyReportPlan, MonthlyReportRecipient], Awaitable[MonthlyReportDispatch | None]
]
Claim = Callable[
    [MonthlyReportPlan, MonthlyReportRecipient], Awaitable[MonthlyReportDispatch | None]
]
Deliver = Callable[
    [MonthlyReportPlan, MonthlyReportRecipient, DispatchKind], Awaitable[str | None]
]
Record = Callable[[uuid.UUID, str | None], Awaitable[MonthlyReportDispatch | None]]


class OutcomeUnconfirmed(Exception):
    """The e-mail may have left; the record stays unconfirmed, never retried."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def make_send_one(claim: Claim, deliver: Deliver, record: Record) -> SendOne:
    """Claim, send, record — each step on its own, so none can undo another."""

    async def send_one(
        plan: MonthlyReportPlan, recipient: MonthlyReportRecipient
    ) -> MonthlyReportDispatch | None:
        dispatch = await claim(plan, recipient)
        if dispatch is None:
            return None
        try:
            error = await deliver(plan, recipient, dispatch.kind)
        except Exception as exc:
            # Only a definite refusal comes back as `error`, safe to retry. An
            # uncertain transfer, or anything unexpected, may have left: the
            # claim stays unconfirmed and the job never sends it again.
            raise OutcomeUnconfirmed(
                f"envio interrompido ({exc.__class__.__name__}: {exc})"
            ) from exc
        try:
            return await record(dispatch.id, error)
        except Exception as exc:
            raise OutcomeUnconfirmed("o resultado não foi registrado") from exc

    return send_one


async def dispatch_all(
    startups: list[Startup], plan_one: PlanOne, send_one: SendOne
) -> DispatchSummary:
    """Visit every startup; an error is reported and the sweep goes on.

    `plan_one` and each step of `send_one` run in a transaction of their own,
    so an unexpected exception here loses only the step that raised it.
    """
    summary = DispatchSummary(startups=len(startups))
    for startup in startups:
        try:
            plan = await plan_one(startup)
        except Exception:
            summary.failed += 1
            print(f"FALHA {startup.name}: erro ao preparar o envio")
            traceback.print_exc()
            continue
        if plan is MonthlyReportSkip.ALREADY_REPORTED:
            continue
        if plan is MonthlyReportSkip.NO_RECIPIENTS:
            # Not a failure of the job, but a gap: say it where the operator
            # reads the run, not only on the startup's page.
            summary.without_recipients += 1
            print(
                f"SEM DESTINATÁRIO {startup.name}: envio mensal ligado, mas nenhum "
                "executivo marcado tem e-mail"
            )
            continue

        for recipient in plan.recipients:
            try:
                record = await send_one(plan, recipient)
            except OutcomeUnconfirmed as exc:
                summary.failed += 1
                print(
                    f"NÃO CONFIRMADO {startup.name} → {recipient.email}: "
                    f"{exc.reason}; o e-mail pode ter saído — confirme antes de reenviar"
                )
                traceback.print_exc()
                continue
            except Exception:
                summary.failed += 1
                print(f"FALHA {startup.name} → {recipient.email}: erro inesperado")
                traceback.print_exc()
                continue
            if record is None:
                continue
            if record.error:
                summary.failed += 1
                print(f"FALHA {startup.name} → {record.recipient_email}: {record.error}")
            else:
                summary.sent += 1
                print(f"ok    {startup.name} → {record.recipient_email} ({record.kind.value})")
    return summary


async def main(kind: DispatchKind, period: Period | None = None) -> None:
    from app.database import async_session, engine

    sender = build_email_sender(settings)

    async def plan_one(startup: Startup) -> MonthlyReportPlan | MonthlyReportSkip:
        async with async_session() as session, session.begin():
            return await PlanMonthlyReport(
                ExecutiveRepository(session), MonthlyIndicatorRepository(session)
            ).execute(startup, kind, period)

    async def claim(
        plan: MonthlyReportPlan, recipient: MonthlyReportRecipient
    ) -> MonthlyReportDispatch | None:
        async with async_session() as session, session.begin():
            return await ClaimMonthlyReportDispatch(
                MonthlyReportDispatchRepository(session)
            ).execute(plan, recipient)

    async def record(
        dispatch_id: uuid.UUID, error: str | None
    ) -> MonthlyReportDispatch | None:
        async with async_session() as session, session.begin():
            return await RecordMonthlyReportOutcome(
                MonthlyReportDispatchRepository(session)
            ).execute(dispatch_id, error)

    deliver = SendMonthlyReport(
        sender, settings.app_base_url, settings.email_signature
    ).execute
    send_one = make_send_one(claim, deliver, record)

    try:
        async with async_session() as session:
            startups = await ListStartupsForMonthlyReport(
                StartupRepository(session)
            ).execute()
        summary = await dispatch_all(startups, plan_one, send_one)
    finally:
        await sender.close()
        await engine.dispose()

    print(
        f"{kind.value}: {summary.startups} startups, "
        f"{summary.sent} enviados, {summary.failed} falhas, "
        f"{summary.without_recipients} sem destinatário"
    )
    if summary.failed:
        # A non-zero exit marks the Cloud Run execution as failed, so it shows up.
        raise SystemExit(1)


def parse_period(value: str) -> Period:
    """`AAAA-MM`, a month already closed."""
    try:
        year, month = (int(part) for part in value.split("-"))
        period = Period(year=year, month=month)
        validate_period_closed(period)
    except InvalidInputError as exc:  # before ValueError, which it subclasses
        raise argparse.ArgumentTypeError(str(exc)) from exc
    except ValueError as exc:  # also Period's own invariant
        raise argparse.ArgumentTypeError(f"período inválido {value!r}: use AAAA-MM") from exc
    return period


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--kind", choices=[k.value for k in DispatchKind], required=True
    )
    parser.add_argument(
        "--period",
        type=parse_period,
        help="mês já fechado, AAAA-MM; padrão: o mês anterior a hoje",
    )
    args = parser.parse_args()
    asyncio.run(main(DispatchKind(args.kind), args.period))
