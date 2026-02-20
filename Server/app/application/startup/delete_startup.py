from app.domain.models.startup import Startup
from app.repositories.startup_repository import StartupRepository


class DeleteStartup:
    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self, startup: Startup) -> None:
        await self._repository.delete(startup)
