from app.domain.exceptions import ConflictError
from app.domain.models.user import User
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from app.repositories.user_repository import UserRepository


class RegisterUser:
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: BcryptPasswordHasher,
    ) -> None:
        self._repository = repository
        self._hasher = password_hasher

    async def execute(
        self, username: str, email: str, password: str
    ) -> User:
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
