import uuid

from app.domain.exceptions import ConflictError
from app.domain.models.user import User
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from app.repositories.user_repository import UserRepository


class UpdateUser:
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: BcryptPasswordHasher,
    ) -> None:
        self._repository = repository
        self._hasher = password_hasher

    async def execute(
        self,
        user: User,
        updates: dict,
        current_user_id: uuid.UUID | None = None,
    ) -> User:
        if (
            "is_active" in updates
            and not updates["is_active"]
            and current_user_id
            and user.id == current_user_id
        ):
            raise ValueError("Voce nao pode desativar seu proprio usuario")

        password = updates.pop("password", None)
        if password:
            user.hashed_password = self._hasher.hash(password)

        username = updates.get("username")
        if username and username != user.username:
            existing = await self._repository.get_by_username(username)
            if existing:
                raise ConflictError(f"Username '{username}' ja esta em uso")

        email = updates.get("email")
        if email and email != user.email:
            existing = await self._repository.get_by_email(email)
            if existing:
                raise ConflictError(f"Email '{email}' ja esta em uso")

        for field, value in updates.items():
            setattr(user, field, value)
        return await self._repository.update(user)
