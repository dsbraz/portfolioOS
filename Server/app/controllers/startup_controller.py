import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.models.startup import Startup
from app.domain.schemas.startup import (
    StartupCreate,
    StartupListResponse,
    StartupResponse,
    StartupUpdate,
)
from app.repositories.startup_repository import StartupRepository
from app.use_cases.base_crud import CrudUseCase

router = APIRouter(prefix="/startups", tags=["Startups"])


def _get_use_case(
    session: AsyncSession = Depends(get_session),
) -> CrudUseCase[Startup]:
    return CrudUseCase(StartupRepository(session))


@router.get("", response_model=StartupListResponse)
async def list_startups(
    use_case: CrudUseCase[Startup] = Depends(_get_use_case),
):
    items, total = await use_case.list_all()
    return StartupListResponse(
        items=[StartupResponse.model_validate(s) for s in items],
        total=total,
    )


@router.get("/{startup_id}", response_model=StartupResponse)
async def get_startup(
    startup_id: uuid.UUID,
    use_case: CrudUseCase[Startup] = Depends(_get_use_case),
):
    startup = await use_case.get_by_id(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    return StartupResponse.model_validate(startup)


@router.post(
    "", response_model=StartupResponse, status_code=status.HTTP_201_CREATED
)
async def create_startup(
    data: StartupCreate,
    use_case: CrudUseCase[Startup] = Depends(_get_use_case),
):
    startup = Startup(**data.model_dump())
    created = await use_case.create(startup)
    return StartupResponse.model_validate(created)


@router.patch("/{startup_id}", response_model=StartupResponse)
async def update_startup(
    startup_id: uuid.UUID,
    data: StartupUpdate,
    use_case: CrudUseCase[Startup] = Depends(_get_use_case),
):
    startup = await use_case.get_by_id(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    updated = await use_case.update(startup, data.model_dump(exclude_unset=True))
    return StartupResponse.model_validate(updated)


@router.delete("/{startup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_startup(
    startup_id: uuid.UUID,
    use_case: CrudUseCase[Startup] = Depends(_get_use_case),
):
    startup = await use_case.get_by_id(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    await use_case.delete(startup)
