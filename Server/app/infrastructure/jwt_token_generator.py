from datetime import datetime, timedelta, timezone

from jose import jwt

from app.domain.models.user import User


class JwtTokenGenerator:
    def __init__(self, secret_key: str, expire_minutes: int = 60) -> None:
        self._secret_key = secret_key
        self._expire_minutes = expire_minutes

    def create_token(self, user: User) -> str:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=self._expire_minutes
        )
        payload = {
            "sub": str(user.id),
            "exp": expire,
        }
        return jwt.encode(payload, self._secret_key, algorithm="HS256")
