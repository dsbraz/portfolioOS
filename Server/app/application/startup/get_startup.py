import uuid

from app.domain.models.startup import Startup
from app.repositories.startup_repository import StartupRepository


class GetStartup:
    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self, startup_id: uuid.UUID) -> Startup | None:
        return await self._repository.get_by_id(startup_id)
