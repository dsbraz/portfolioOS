import uuid
from datetime import UTC, datetime

from app.domain.exceptions import ConflictError
from app.domain.models.user import User
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from app.repositories.user_invite_repository import UserInviteRepository
from app.repositories.user_repository import UserRepository


class ConsumeUserInvite:
    def __init__(
        self,
        invite_repository: UserInviteRepository,
        user_repository: UserRepository,
        password_hasher: BcryptPasswordHasher,
    ) -> None:
        self._invite_repository = invite_repository
        self._user_repository = user_repository
        self._hasher = password_hasher

    async def execute(
        self,
        token: uuid.UUID,
        email: str,
        username: str,
        password: str,
    ) -> User | None:
        invite = await self._invite_repository.get_by_token(token)
        if not invite:
            return None

        now = datetime.now(UTC)
        if invite.expires_at.tzinfo is None:
            now = now.replace(tzinfo=None)
        if invite.used_at is not None or invite.expires_at <= now:
            return None

        if invite.email.strip().lower() != email.strip().lower():
            raise ValueError("Email do convite invalido")

        existing_username = await self._user_repository.get_by_username(
            username
        )
        if existing_username:
            raise ConflictError(f"Username '{username}' ja esta em uso")

        existing_email = await self._user_repository.get_by_email(invite.email)
        if existing_email:
            raise ConflictError(f"Email '{invite.email}' ja esta em uso")

        user = User(
            username=username,
            email=invite.email,
            hashed_password=self._hasher.hash(password),
        )
        created_user = await self._user_repository.create(user)
        await self._invite_repository.mark_used(invite, now)
        return created_user
