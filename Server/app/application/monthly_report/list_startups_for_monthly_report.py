from app.domain.models.startup import Startup
from app.domain.repositories import StartupRepository


class ListStartupsForMonthlyReport:
    """The startups the monthly job visits: only those that opted in."""

    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self) -> list[Startup]:
        return await self._repository.get_all_with_monthly_report_enabled()
