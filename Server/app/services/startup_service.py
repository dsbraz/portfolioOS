import uuid

from app.domain.models.startup import Startup
from app.repositories.startup_repository import StartupRepository


class StartupService:
    def __init__(self, repository: StartupRepository):
        self._repository = repository

    async def list_startups(self) -> tuple[list[Startup], int]:
        return await self._repository.get_all()

    async def get_startup(self, startup_id: uuid.UUID) -> Startup | None:
        return await self._repository.get_by_id(startup_id)

    async def create_startup(self, startup: Startup) -> Startup:
        return await self._repository.create(startup)

    async def update_startup(
        self, startup: Startup, updates: dict
    ) -> Startup:
        for field, value in updates.items():
            setattr(startup, field, value)
        return await self._repository.update(startup)

    async def delete_startup(self, startup: Startup) -> None:
        await self._repository.delete(startup)
