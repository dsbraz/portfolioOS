from app.domain.models.user import User
from app.infrastructure.jwt_token_generator import JwtTokenGenerator


class CreateAccessToken:
    def __init__(self, token_generator: JwtTokenGenerator) -> None:
        self._token_generator = token_generator

    def execute(self, user: User) -> str:
        return self._token_generator.create_token(user)
