import uuid

from app.domain.models.executive import Executive
from app.repositories.executive_repository import ExecutiveRepository


class ExecutiveService:
    def __init__(self, repository: ExecutiveRepository):
        self._repository = repository

    async def list_executives(
        self, startup_id: uuid.UUID
    ) -> tuple[list[Executive], int]:
        return await self._repository.get_all_by_startup(startup_id)

    async def get_executive(self, executive_id: uuid.UUID) -> Executive | None:
        return await self._repository.get_by_id(executive_id)

    async def create_executive(self, executive: Executive) -> Executive:
        return await self._repository.create(executive)

    async def update_executive(
        self, executive: Executive, updates: dict
    ) -> Executive:
        for field, value in updates.items():
            setattr(executive, field, value)
        return await self._repository.update(executive)

    async def delete_executive(self, executive: Executive) -> None:
        await self._repository.delete(executive)
