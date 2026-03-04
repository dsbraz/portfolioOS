from datetime import UTC, datetime, timedelta

from app.domain.exceptions import ConflictError
from app.domain.models.user_invite import UserInvite
from app.repositories.user_invite_repository import UserInviteRepository
from app.repositories.user_repository import UserRepository


INVITE_TTL_HOURS = 72


class CreateUserInvite:
    def __init__(
        self,
        invite_repository: UserInviteRepository,
        user_repository: UserRepository,
    ) -> None:
        self._invite_repository = invite_repository
        self._user_repository = user_repository

    async def execute(self, email: str) -> UserInvite:
        existing_user = await self._user_repository.get_by_email(email)
        if existing_user:
            raise ConflictError(f"Email '{email}' ja esta em uso")

        now = datetime.now(UTC)
        active_invite = await self._invite_repository.get_active_by_email(
            email, now
        )
        if active_invite:
            await self._invite_repository.revoke(active_invite, now)

        invite = UserInvite(
            email=email,
            expires_at=now + timedelta(hours=INVITE_TTL_HOURS),
        )
        return await self._invite_repository.create(invite)
