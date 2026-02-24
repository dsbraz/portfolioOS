from app.domain.models.user import User
from app.repositories.user_repository import UserRepository


class ListUsers:
    def __init__(self, repository: UserRepository) -> None:
        self._repository = repository

    async def execute(self) -> tuple[list[User], int]:
        return await self._repository.get_all()
