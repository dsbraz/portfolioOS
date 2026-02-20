import uuid
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class CrudUseCase(Generic[T]):
    """Generic use case for standard CRUD operations.

    Works with any repository that exposes ``get_by_id``, ``create``,
    ``update`` and ``delete`` methods.  Listing is intentionally split
    into ``list_all`` (top-level entities) and ``list_by_parent``
    (child entities) because their signatures differ.
    """

    def __init__(self, repository: Any) -> None:
        self._repository = repository

    async def list_all(self) -> tuple[list[T], int]:
        return await self._repository.get_all()

    async def list_by_parent(
        self, parent_id: uuid.UUID
    ) -> tuple[list[T], int]:
        return await self._repository.get_all_by_startup(parent_id)

    async def get_by_id(self, entity_id: uuid.UUID) -> T | None:
        return await self._repository.get_by_id(entity_id)

    async def create(self, entity: T) -> T:
        return await self._repository.create(entity)

    async def update(self, entity: T, updates: dict) -> T:
        for field, value in updates.items():
            setattr(entity, field, value)
        return await self._repository.update(entity)

    async def delete(self, entity: T) -> None:
        await self._repository.delete(entity)
