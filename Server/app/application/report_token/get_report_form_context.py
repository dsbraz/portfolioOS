from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.report_token import ReportToken
from app.domain.models.startup import Startup
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)
from app.repositories.startup_repository import StartupRepository


class GetReportFormContext:
    def __init__(
        self,
        startup_repo: StartupRepository,
        indicator_repo: MonthlyIndicatorRepository,
    ) -> None:
        self._startup_repo = startup_repo
        self._indicator_repo = indicator_repo

    async def execute(
        self, report_token: ReportToken
    ) -> tuple[Startup | None, MonthlyIndicator | None]:
        startup = await self._startup_repo.get_by_id(
            report_token.startup_id
        )
        indicator = await self._indicator_repo.get_by_startup_and_period(
            report_token.startup_id,
            report_token.month,
            report_token.year,
        )
        return startup, indicator
