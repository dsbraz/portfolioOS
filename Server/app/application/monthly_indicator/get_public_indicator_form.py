from app.domain.models.monthly_indicator import MonthlyIndicator
from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken
from app.domain.models.startup import Startup
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.startup_repository import StartupRepository


class GetPublicIndicatorForm:
    def __init__(
        self,
        startup_repo: StartupRepository,
        indicator_repo: MonthlyIndicatorRepository,
    ) -> None:
        self._startup_repo = startup_repo
        self._indicator_repo = indicator_repo

    async def execute(
        self, token: MonthlyIndicatorToken
    ) -> tuple[Startup | None, MonthlyIndicator | None]:
        startup = await self._startup_repo.get_by_id(token.startup_id)
        indicator = await self._indicator_repo.get_by_startup_and_period(
            token.startup_id, token.month, token.year
        )
        return startup, indicator
