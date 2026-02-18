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
from app.services.executive_service import ExecutiveService

router = APIRouter(prefix="/startups/{startup_id}/executives", tags=["Executives"])


def _get_service(session: AsyncSession = Depends(get_session)) -> ExecutiveService:
    return ExecutiveService(ExecutiveRepository(session))


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
    service: ExecutiveService = Depends(_get_service),
):
    items, total = await service.list_executives(startup_id)
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
    service: ExecutiveService = Depends(_get_service),
):
    executive = Executive(startup_id=startup_id, **data.model_dump())
    created = await service.create_executive(executive)
    return ExecutiveResponse.model_validate(created)


@router.get("/{executive_id}", response_model=ExecutiveResponse)
async def get_executive(
    executive_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: ExecutiveService = Depends(_get_service),
):
    executive = await service.get_executive(executive_id)
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
    service: ExecutiveService = Depends(_get_service),
):
    executive = await service.get_executive(executive_id)
    if not executive or executive.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executivo com id {executive_id} não encontrado",
        )
    updated = await service.update_executive(executive, data.model_dump(exclude_unset=True))
    return ExecutiveResponse.model_validate(updated)


@router.delete("/{executive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_executive(
    executive_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: ExecutiveService = Depends(_get_service),
):
    executive = await service.get_executive(executive_id)
    if not executive or executive.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executivo com id {executive_id} não encontrado",
        )
    await service.delete_executive(executive)
