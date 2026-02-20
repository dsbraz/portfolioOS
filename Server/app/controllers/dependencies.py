import uuid
from typing import Callable, TypeVar

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.startup.get_startup import GetStartup
from app.database import get_session
from app.repositories.board_meeting_repository import BoardMeetingRepository
from app.repositories.deal_repository import DealRepository
from app.repositories.executive_repository import ExecutiveRepository
from app.repositories.monthly_indicator_repository import MonthlyIndicatorRepository
from app.repositories.startup_repository import StartupRepository

T = TypeVar("T")


def use_case_builder(repo_class: type) -> Callable:
    """Create a use-case factory bound to a shared repository dependency.

    Internally creates a repository dependency from *repo_class* so that
    every use-case produced by the returned ``_builder`` callable shares
    the same repository instance (and therefore DB session) per request,
    thanks to FastAPI's dependency cache.

    Usage inside a controller module::

        _builder = use_case_builder(DealRepository)

        @router.get("")
        async def list_deals(use_case: ListDeals = Depends(_builder(ListDeals))):
            ...
    """

    def _get_repo(session: AsyncSession = Depends(get_session)):  # noqa: ANN202
        return repo_class(session)

    def _builder(uc_class: type[T]) -> Callable[..., T]:
        def factory(repo=Depends(_get_repo)):  # noqa: ANN001
            return uc_class(repo)

        return factory

    return _builder


startup_builder = use_case_builder(StartupRepository)
deal_builder = use_case_builder(DealRepository)
board_meeting_builder = use_case_builder(BoardMeetingRepository)
executive_builder = use_case_builder(ExecutiveRepository)
monthly_indicator_builder = use_case_builder(MonthlyIndicatorRepository)


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
