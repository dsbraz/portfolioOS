from app.domain.exceptions import ConflictError
from app.domain.models.user import User
from app.domain.password_hasher import PasswordHasher
from app.domain.validators import (
    validate_password_max_bytes,
    validate_username_no_spaces,
)
from app.repositories.user_repository import UserRepository


class RegisterUser:
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: PasswordHasher,
    ) -> None:
        self._repository = repository
        self._hasher = password_hasher

    async def execute(self, username: str, email: str, password: str) -> User:
        validate_username_no_spaces(username)
        validate_password_max_bytes(password)

        existing = await self._repository.get_by_username(username)
        if existing:
            raise ConflictError(f"Username '{username}' ja esta em uso")

        existing = await self._repository.get_by_email(email)
        if existing:
            raise ConflictError(f"Email '{email}' ja esta em uso")

        user = User(
            username=username,
            email=email,
            hashed_password=self._hasher.hash(password),
        )
        return await self._repository.create(user)
