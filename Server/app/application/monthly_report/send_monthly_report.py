from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
)
from app.domain.email_sender import EmailDeliveryError, EmailSender
from app.domain.models.monthly_report_dispatch import (
    DispatchKind,
    MonthlyReportDispatch,
)
from app.domain.reporting_message import build_reporting_email
from app.domain.repositories import MonthlyReportDispatchRepository


class SendMonthlyReport:
    """E-mail one recipient of a plan, and record it.

    The job runs this in a transaction per recipient, so the record of a mail
    that left is committed right after it — a later failure cannot undo it, and
    a rerun skips it. A send that failed before is retried.
    """

    def __init__(
        self,
        dispatch_repository: MonthlyReportDispatchRepository,
        email_sender: EmailSender,
        app_base_url: str,
        signature: str | None = None,
    ) -> None:
        self._dispatch_repository = dispatch_repository
        self._email_sender = email_sender
        self._app_base_url = app_base_url.rstrip("/")
        self._signature = signature

    async def execute(
        self, plan: MonthlyReportPlan, recipient: MonthlyReportRecipient
    ) -> MonthlyReportDispatch | None:
        kind = await self._effective_kind(plan, recipient)
        dispatch, created = await self._dispatch_repository.get_or_create(
            MonthlyReportDispatch(
                startup_id=plan.startup_id,
                executive_id=recipient.executive_id,
                recipient_email=recipient.email,
                month=plan.period.month,
                year=plan.period.year,
                kind=kind,
            )
        )
        if not created and dispatch.error is None:
            return None

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
            error = None
        except EmailDeliveryError as exc:
            error = str(exc) or exc.__class__.__name__

        if not created or error is not None:
            # A retry goes to the address on record now, and the history says so.
            dispatch.recipient_email = recipient.email
            dispatch.error = error
            dispatch = await self._dispatch_repository.update(dispatch)
        return dispatch

    async def _effective_kind(
        self, plan: MonthlyReportPlan, recipient: MonthlyReportRecipient
    ) -> DispatchKind:
        """A reminder only reminds someone who got the request.

        The send may have been switched on after day 10, the executive marked
        later, or the first e-mail may have failed: "we still have not received
        it" would then refer to a message they never saw. They get the first
        e-mail instead, recorded as such.
        """
        if plan.kind is not DispatchKind.REMINDER:
            return plan.kind
        initial = await self._dispatch_repository.find(
            plan.startup_id,
            recipient.executive_id,
            plan.period.month,
            plan.period.year,
            DispatchKind.INITIAL,
        )
        if initial is None or initial.error is not None:
            return DispatchKind.INITIAL
        return DispatchKind.REMINDER
