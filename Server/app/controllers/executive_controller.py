import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.models.executive import Executive
from app.domain.schemas.executive import (
    ExecutiveCreate,
    ExecutiveListResponse,
    ExecutiveResponse,
    ExecutiveUpdate,
)
from app.repositories.executive_repository import ExecutiveRepository
from app.repositories.startup_repository import StartupRepository
from app.use_cases.base_crud import CrudUseCase

router = APIRouter(prefix="/startups/{startup_id}/executives", tags=["Executives"])


def _get_use_case(
    session: AsyncSession = Depends(get_session),
) -> CrudUseCase[Executive]:
    return CrudUseCase(ExecutiveRepository(session))


def _get_startup_repo(session: AsyncSession = Depends(get_session)) -> StartupRepository:
    return StartupRepository(session)


async def _verify_startup_exists(
    startup_id: uuid.UUID,
    startup_repo: StartupRepository = Depends(_get_startup_repo),
) -> uuid.UUID:
    startup = await startup_repo.get_by_id(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    return startup_id


@router.get("", response_model=ExecutiveListResponse)
async def list_executives(
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    use_case: CrudUseCase[Executive] = Depends(_get_use_case),
):
    items, total = await use_case.list_by_parent(startup_id)
    return ExecutiveListResponse(
        items=[ExecutiveResponse.model_validate(e) for e in items],
        total=total,
    )


@router.post(
    "", response_model=ExecutiveResponse, status_code=status.HTTP_201_CREATED
)
async def create_executive(
    data: ExecutiveCreate,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    use_case: CrudUseCase[Executive] = Depends(_get_use_case),
):
    executive = Executive(startup_id=startup_id, **data.model_dump())
    created = await use_case.create(executive)
    return ExecutiveResponse.model_validate(created)


@router.get("/{executive_id}", response_model=ExecutiveResponse)
async def get_executive(
    executive_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    use_case: CrudUseCase[Executive] = Depends(_get_use_case),
):
    executive = await use_case.get_by_id(executive_id)
    if not executive or executive.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executivo com id {executive_id} não encontrado",
        )
    return ExecutiveResponse.model_validate(executive)


@router.patch("/{executive_id}", response_model=ExecutiveResponse)
async def update_executive(
    executive_id: uuid.UUID,
    data: ExecutiveUpdate,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    use_case: CrudUseCase[Executive] = Depends(_get_use_case),
):
    executive = await use_case.get_by_id(executive_id)
    if not executive or executive.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executivo com id {executive_id} não encontrado",
        )
    updated = await use_case.update(executive, data.model_dump(exclude_unset=True))
    return ExecutiveResponse.model_validate(updated)


@router.delete("/{executive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_executive(
    executive_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    use_case: CrudUseCase[Executive] = Depends(_get_use_case),
):
    executive = await use_case.get_by_id(executive_id)
    if not executive or executive.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executivo com id {executive_id} não encontrado",
        )
    await use_case.delete(executive)
