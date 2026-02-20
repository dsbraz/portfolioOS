from app.domain.models.startup import Startup
from app.repositories.startup_repository import StartupRepository


class UpdateStartup:
    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self, startup: Startup, updates: dict) -> Startup:
        for field, value in updates.items():
            setattr(startup, field, value)
        return await self._repository.update(startup)
