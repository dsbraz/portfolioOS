import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.domain.exceptions import ConflictError
from app.domain.models.user import User
from app.repositories.user_repository import UserRepository

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    def __init__(
        self,
        repository: UserRepository,
        secret_key: str,
        token_expire_minutes: int = 60,
    ):
        self._repository = repository
        self._secret_key = secret_key
        self._token_expire_minutes = token_expire_minutes

    async def register(
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
            hashed_password=pwd_context.hash(password),
        )
        return await self._repository.create(user)

    async def authenticate(
        self, username: str, password: str
    ) -> User | None:
        user = await self._repository.get_by_username(username)
        if not user:
            return None
        if not pwd_context.verify(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    async def update_user(
        self, user: User, updates: dict, current_user_id: uuid.UUID | None = None
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
            user.hashed_password = pwd_context.hash(password)

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

    def create_access_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self._token_expire_minutes
        )
        payload = {
            "sub": str(user.id),
            "exp": expire,
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")
