from app.domain.exceptions import InvalidInputError
from app.domain.models.startup import Startup
from app.domain.repositories import StartupRepository


class UpdateStartup:
    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self, startup: Startup, updates: dict) -> Startup:
        investment_date = updates.get("investment_date")
        # The same rule `RecordStartupExit` checks, from the other side.
        if (
            investment_date is not None
            and startup.exited_on is not None
            and investment_date > startup.exited_on
        ):
            raise InvalidInputError(
                "Data do investimento não pode ser posterior à saída"
            )

        for field, value in updates.items():
            setattr(startup, field, value)
        return await self._repository.update(startup)
