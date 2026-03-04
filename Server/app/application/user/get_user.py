import uuid

from app.domain.models.user import User
from app.repositories.user_repository import UserRepository


class GetUser:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self, user_id: uuid.UUID) -> User | None:
        return await self._repository.get_by_id(user_id)
