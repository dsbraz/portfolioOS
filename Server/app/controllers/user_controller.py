import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.controllers.auth_dependency import get_current_user
from app.database import get_session
from app.domain.exceptions import ConflictError
from app.domain.models.user import User
from app.domain.schemas.user import (
    UserCreate,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(tags=["Users"])


def _get_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(
        UserRepository(session),
        settings.secret_key,
        settings.access_token_expire_minutes,
    )


async def _get_user_or_404(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuario com id {user_id} nao encontrado",
        )
    return user


@router.post(
    "/users",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    data: UserCreate,
    service: AuthService = Depends(_get_service),
):
    try:
        user = await service.register(
            data.username, data.email, data.password
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    return UserResponse.model_validate(user)


@router.get(
    "/users",
    response_model=UserListResponse,
)
async def list_users(
    session: AsyncSession = Depends(get_session),
):
    repo = UserRepository(session)
    items, total = await repo.get_all()
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in items],
        total=total,
    )


@router.patch(
    "/users/{user_id}",
    response_model=UserResponse,
)
async def update_user(
    data: UserUpdate,
    user=Depends(_get_user_or_404),
    current_user: User = Depends(get_current_user),
    service: AuthService = Depends(_get_service),
):
    try:
        updated = await service.update_user(
            user, data.model_dump(exclude_unset=True), current_user.id
        )
    except ConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return UserResponse.model_validate(updated)
