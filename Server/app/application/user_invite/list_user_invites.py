from datetime import UTC, datetime

from app.domain.models.user_invite import UserInvite
from app.repositories.user_invite_repository import UserInviteRepository


class ListUserInvites:
    def __init__(self, repository: UserInviteRepository) -> None:
        self._repository = repository

    async def execute(self) -> tuple[list[UserInvite], int]:
        now = datetime.now(UTC)
        return await self._repository.get_all_active(now)
