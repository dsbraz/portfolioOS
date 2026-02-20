from app.domain.models.user import User
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from app.repositories.user_repository import UserRepository


class AuthenticateUser:
    def __init__(
        self,
        repository: UserRepository,
        password_hasher: BcryptPasswordHasher,
    ) -> None:
        self._repository = repository
        self._hasher = password_hasher

    async def execute(self, username: str, password: str) -> User | None:
        user = await self._repository.get_by_username(username)
        if not user:
            return None
        if not self._hasher.verify(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user
