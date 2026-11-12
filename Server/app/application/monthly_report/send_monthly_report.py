from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
)
from app.domain.email_sender import EmailDeliveryError, EmailSender
from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.reporting_message import build_reporting_email


class SendMonthlyReport:
    """E-mail one recipient: the network call between claim and outcome.

    No repository: it runs outside any transaction, so a slow relay holds no
    database connection. Returns why the relay refused the message, or `None`
    when it left.
    """

    def __init__(
        self,
        email_sender: EmailSender,
        app_base_url: str,
        signature: str | None = None,
    ) -> None:
        self._email_sender = email_sender
        self._app_base_url = app_base_url.rstrip("/")
        self._signature = signature

    async def execute(
        self,
        plan: MonthlyReportPlan,
        recipient: MonthlyReportRecipient,
        kind: DispatchKind,
    ) -> str | None:
        message = build_reporting_email(
            kind,
            recipient.name,
            plan.startup_name,
            plan.period.month,
            plan.period.year,
            f"{self._app_base_url}/monthly-indicator/{plan.form_token}",
            self._signature,
        )
        try:
            await self._email_sender.send(recipient.email, message.subject, message.body)
        except EmailDeliveryError as exc:
            return str(exc) or exc.__class__.__name__
        return None
