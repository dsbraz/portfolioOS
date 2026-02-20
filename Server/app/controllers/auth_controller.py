from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.domain.schemas.auth import LoginRequest, TokenResponse
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from app.infrastructure.jwt_token_generator import JwtTokenGenerator
from app.repositories.user_repository import UserRepository
from app.use_cases.auth.authenticate_user import AuthenticateUser
from app.use_cases.auth.create_access_token import CreateAccessToken

router = APIRouter(tags=["Auth"])

_hasher = BcryptPasswordHasher()
_token_gen = JwtTokenGenerator(
    settings.secret_key, settings.access_token_expire_minutes
)


def _get_authenticate(
    session: AsyncSession = Depends(get_session),
) -> AuthenticateUser:
    return AuthenticateUser(UserRepository(session), _hasher)


def _get_create_token() -> CreateAccessToken:
    return CreateAccessToken(_token_gen)


@router.post(
    "/auth/login",
    response_model=TokenResponse,
)
async def login(
    data: LoginRequest,
    authenticate: AuthenticateUser = Depends(_get_authenticate),
    create_token: CreateAccessToken = Depends(_get_create_token),
):
    user = await authenticate.execute(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    token = create_token.execute(user)
    return TokenResponse(access_token=token)
