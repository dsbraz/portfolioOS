import uuid
from datetime import UTC, datetime

from app.domain.models.monthly_report_dispatch import MonthlyReportDispatch
from app.domain.repositories import MonthlyReportDispatchRepository


class RecordMonthlyReportOutcome:
    """Mark a claimed send as delivered, or as failed with the reason.

    A failure is retried by the next run; a delivery dates the history with the
    moment the relay accepted the message, not the moment it was claimed.
    """

    def __init__(self, dispatch_repository: MonthlyReportDispatchRepository) -> None:
        self._dispatch_repository = dispatch_repository

    async def execute(
        self, dispatch_id: uuid.UUID, error: str | None
    ) -> MonthlyReportDispatch | None:
        dispatch = await self._dispatch_repository.get_by_id(dispatch_id)
        if dispatch is None:
            return None
        if error is None:
            dispatch.sent_at = datetime.now(UTC)
            dispatch.error = None
        else:
            dispatch.sent_at = None
            dispatch.error = error
        return await self._dispatch_repository.update(dispatch)
