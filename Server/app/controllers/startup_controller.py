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
from app.services.startup_service import StartupService

router = APIRouter(prefix="/startups", tags=["Startups"])


def _get_service(session: AsyncSession = Depends(get_session)) -> StartupService:
    return StartupService(StartupRepository(session))


@router.get("", response_model=StartupListResponse)
async def list_startups(service: StartupService = Depends(_get_service)):
    items, total = await service.list_startups()
    return StartupListResponse(
        items=[StartupResponse.model_validate(s) for s in items],
        total=total,
    )


@router.get("/{startup_id}", response_model=StartupResponse)
async def get_startup(
    startup_id: uuid.UUID, service: StartupService = Depends(_get_service)
):
    startup = await service.get_startup(startup_id)
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
    service: StartupService = Depends(_get_service),
):
    startup = Startup(**data.model_dump())
    created = await service.create_startup(startup)
    return StartupResponse.model_validate(created)


@router.patch("/{startup_id}", response_model=StartupResponse)
async def update_startup(
    startup_id: uuid.UUID,
    data: StartupUpdate,
    service: StartupService = Depends(_get_service),
):
    startup = await service.get_startup(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    updated = await service.update_startup(startup, data.model_dump(exclude_unset=True))
    return StartupResponse.model_validate(updated)


@router.delete("/{startup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_startup(
    startup_id: uuid.UUID,
    service: StartupService = Depends(_get_service),
):
    startup = await service.get_startup(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    await service.delete_startup(startup)
