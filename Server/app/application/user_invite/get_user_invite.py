import uuid
from datetime import UTC, datetime

from app.domain.models.user_invite import UserInvite
from app.repositories.user_invite_repository import UserInviteRepository


class GetUserInvite:
    def __init__(self, repository: UserInviteRepository) -> None:
        self._repository = repository

    async def execute(self, token: uuid.UUID) -> UserInvite | None:
        invite = await self._repository.get_by_token(token)
        if not invite:
            return None

        now = datetime.now(UTC)
        if invite.expires_at.tzinfo is None:
            now = now.replace(tzinfo=None)
        if invite.used_at is not None or invite.expires_at <= now:
            return None

        return invite
