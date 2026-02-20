import uuid

from app.domain.models.report_token import ReportToken
from app.domain.validators import validate_period_not_future
from app.repositories.report_token_repository import ReportTokenRepository


class GenerateReportToken:
    def __init__(
        self, repository: ReportTokenRepository
    ) -> None:
        self._repository = repository

    async def execute(
        self, startup_id: uuid.UUID, month: int, year: int
    ) -> ReportToken:
        validate_period_not_future(month, year)

        existing = await self._repository.get_by_startup_and_period(
            startup_id, month, year
        )
        if existing:
            return existing

        new_token = ReportToken(
            startup_id=startup_id, month=month, year=year
        )
        return await self._repository.create(new_token)
