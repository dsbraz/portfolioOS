from app.domain.models.startup import Startup
from app.repositories.startup_repository import StartupRepository


class CreateStartup:
    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self, startup: Startup) -> Startup:
        return await self._repository.create(startup)
