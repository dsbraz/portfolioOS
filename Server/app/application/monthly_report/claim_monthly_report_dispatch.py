from datetime import UTC, datetime

from app.application.monthly_report.readmodels import (
    MonthlyReportPlan,
    MonthlyReportRecipient,
)
from app.domain.models.monthly_report_dispatch import (
    DispatchKind,
    MonthlyReportDispatch,
)
from app.domain.repositories import MonthlyReportDispatchRepository


class ClaimMonthlyReportDispatch:
    """Decide which e-mail a recipient gets, and record it before it leaves.

    The job commits the claim, sends outside any transaction and then records
    the outcome (`RecordMonthlyReportOutcome`). If the outcome is lost — the
    process dies, the database drops — the row stays unconfirmed and is never
    resent automatically: a missing e-mail shows up in the history, a duplicate
    lands in an executive's inbox.

    `None` when there is nothing to send: already delivered, still
    unconfirmed, or a reminder that would arrive too soon after the request.
    """

    def __init__(self, dispatch_repository: MonthlyReportDispatchRepository) -> None:
        self._dispatch_repository = dispatch_repository

    async def execute(
        self, plan: MonthlyReportPlan, recipient: MonthlyReportRecipient
    ) -> MonthlyReportDispatch | None:
        now = datetime.now(UTC)
        kind = await self._effective_kind(plan, recipient, now)
        if kind is None:
            return None

        dispatch, created = await self._dispatch_repository.get_or_create(
            MonthlyReportDispatch(
                startup_id=plan.startup_id,
                executive_id=recipient.executive_id,
                recipient_email=recipient.email,
                month=plan.period.month,
                year=plan.period.year,
                kind=kind,
                attempted_at=now,
            )
        )
        if created:
            return dispatch
        if not dispatch.failed:
            return None

        # A failed send is retried, and the history shows this attempt.
        dispatch.executive_id = recipient.executive_id
        dispatch.error = None
        dispatch.attempted_at = now
        return await self._dispatch_repository.update(dispatch)

    async def _effective_kind(
        self,
        plan: MonthlyReportPlan,
        recipient: MonthlyReportRecipient,
        now: datetime,
    ) -> DispatchKind | None:
        """A reminder only reminds an inbox that got the request, on an earlier day.

        The send may have been switched on after day 10, the executive marked or
        their address changed later, or the first e-mail may have failed: "we
        still have not received it" would then refer to a message they never
        saw, so that inbox gets the first e-mail instead, recorded as such.

        A request that went out today — this reminder run sent it as the
        replacement, and is now being rerun — is not followed by a reminder
        minutes later. An unconfirmed request is reminded: the reminder carries
        the same link, and is the safe way to make sure it arrived.
        """
        if plan.kind is not DispatchKind.REMINDER:
            return plan.kind
        initial = await self._dispatch_repository.find(
            plan.startup_id,
            recipient.email,
            plan.period.month,
            plan.period.year,
            DispatchKind.INITIAL,
        )
        if initial is None or initial.failed:
            return DispatchKind.INITIAL
        if initial.attempted_at.astimezone(UTC).date() >= now.date():
            return None
        return DispatchKind.REMINDER
