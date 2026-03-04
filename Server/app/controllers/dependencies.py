import uuid
from typing import Callable, TypeVar

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.startup.get_startup import GetStartup
from app.database import get_session
from app.infrastructure.bcrypt_password_hasher import BcryptPasswordHasher
from app.repositories.board_meeting_repository import BoardMeetingRepository
from app.repositories.deal_repository import DealRepository
from app.repositories.executive_repository import ExecutiveRepository
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.startup_repository import StartupRepository
from app.repositories.user_invite_repository import UserInviteRepository
from app.repositories.user_repository import UserRepository

T = TypeVar("T")


def _use_case_builder(repo_class: type) -> Callable:
    """Use case factory for single-repo use cases."""

    def _get_repo(session: AsyncSession = Depends(get_session)):  # noqa: ANN202
        return repo_class(session)

    def _builder(uc_class: type[T]) -> Callable[..., T]:
        def factory(repo=Depends(_get_repo)):  # noqa: ANN001
            return uc_class(repo)

        return factory

    return _builder


def _multi_repo_use_case_builder(*repo_classes: type) -> Callable:
    """Use case factory for multi-repo use cases."""

    def _builder(uc_class: type[T]) -> Callable[..., T]:
        def factory(session: AsyncSession = Depends(get_session)):  # noqa: ANN202
            repos = [cls(session) for cls in repo_classes]
            return uc_class(*repos)

        return factory

    return _builder


def _multi_repo_use_case_with_hasher_builder(
    *repo_classes: type,
) -> Callable:
    """Use case factory for multi-repo use cases with password hasher."""

    def _builder(uc_class: type[T]) -> Callable[..., T]:
        def factory(
            session: AsyncSession = Depends(get_session),
            hasher: BcryptPasswordHasher = Depends(_get_password_hasher),
        ):  # noqa: ANN202
            repos = [cls(session) for cls in repo_classes]
            return uc_class(*repos, hasher)

        return factory

    return _builder


startup_builder = _use_case_builder(StartupRepository)
deal_builder = _use_case_builder(DealRepository)
board_meeting_builder = _use_case_builder(BoardMeetingRepository)
executive_builder = _use_case_builder(ExecutiveRepository)
monthly_indicator_builder = _use_case_builder(MonthlyIndicatorRepository)
portfolio_builder = _multi_repo_use_case_builder(
    StartupRepository, MonthlyIndicatorRepository, BoardMeetingRepository
)
public_form_builder = _multi_repo_use_case_builder(
    StartupRepository, MonthlyIndicatorRepository
)
user_builder = _use_case_builder(UserRepository)
user_invite_builder = _use_case_builder(UserInviteRepository)
user_invite_create_builder = _multi_repo_use_case_builder(
    UserInviteRepository, UserRepository
)


def _get_password_hasher() -> BcryptPasswordHasher:
    return BcryptPasswordHasher()


user_invite_consume_builder = _multi_repo_use_case_with_hasher_builder(
    UserInviteRepository, UserRepository
)


async def verify_startup_exists(
    startup_id: uuid.UUID,
    get_uc: GetStartup = Depends(startup_builder(GetStartup)),
) -> uuid.UUID:
    """Validate that a startup exists; return its id or raise 404."""
    startup = await get_uc.execute(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    return startup_id
