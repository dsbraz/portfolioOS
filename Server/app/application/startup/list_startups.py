from app.domain.models.startup import Startup
from app.repositories.startup_repository import StartupRepository


class ListStartups:
    def __init__(self, repository: StartupRepository) -> None:
        self._repository = repository

    async def execute(self) -> tuple[list[Startup], int]:
        return await self._repository.get_all()
