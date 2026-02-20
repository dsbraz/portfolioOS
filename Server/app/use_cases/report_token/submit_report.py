from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.report_token import ReportToken
from app.repositories.monthly_indicator_repository import (
    MonthlyIndicatorRepository,
)


class SubmitReport:
    def __init__(
        self, indicator_repo: MonthlyIndicatorRepository
    ) -> None:
        self._indicator_repo = indicator_repo

    async def execute(
        self, report_token: ReportToken, data: dict
    ) -> None:
        indicator = await self._indicator_repo.get_by_startup_and_period(
            report_token.startup_id,
            report_token.month,
            report_token.year,
        )

        if indicator:
            for field, value in data.items():
                setattr(indicator, field, value)
            await self._indicator_repo.update(indicator)
        else:
            new_indicator = MonthlyIndicator(
                startup_id=report_token.startup_id,
                month=report_token.month,
                year=report_token.year,
                **data,
            )
            await self._indicator_repo.create(new_indicator)
