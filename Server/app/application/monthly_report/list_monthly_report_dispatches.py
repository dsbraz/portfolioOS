import uuid

from app.domain.models.monthly_report_dispatch import MonthlyReportDispatch
from app.domain.repositories import MonthlyReportDispatchRepository


class ListMonthlyReportDispatches:
    def __init__(self, repository: MonthlyReportDispatchRepository) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID
    ) -> tuple[list[MonthlyReportDispatch], int]:
        return await self._repository.get_all_by_startup(startup_id)
