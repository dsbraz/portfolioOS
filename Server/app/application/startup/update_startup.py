from app.domain.models.startup import Startup
from app.domain.repositories import StartupRepository
from app.domain.validators import validate_exit_not_before_investment


class UpdateStartup:
    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self, startup: Startup, updates: dict) -> Startup:
        investment_date = updates.get("investment_date")
        if investment_date is not None and startup.exited_on is not None:
            validate_exit_not_before_investment(investment_date, startup.exited_on)

        for field, value in updates.items():
            setattr(startup, field, value)
        return await self._repository.update(startup)
