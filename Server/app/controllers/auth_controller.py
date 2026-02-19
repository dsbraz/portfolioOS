from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.domain.schemas.auth import LoginRequest, TokenResponse
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(tags=["Auth"])


def _get_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(
        UserRepository(session),
        settings.secret_key,
        settings.access_token_expire_minutes,
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
)
async def login(
    data: LoginRequest,
    service: AuthService = Depends(_get_service),
):
    user = await service.authenticate(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais invalidas",
        )
    token = service.create_access_token(user)
    return TokenResponse(access_token=token)
