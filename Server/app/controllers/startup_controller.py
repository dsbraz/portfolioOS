import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.startup.create_startup import CreateStartup
from app.application.startup.delete_startup import DeleteStartup
from app.application.startup.get_startup import GetStartup
from app.application.startup.list_startups import ListStartups
from app.application.startup.update_startup import UpdateStartup
from app.controllers.dependencies import startup_builder
from app.domain.models.startup import Startup
from app.domain.schemas.startup import (
    StartupCreate,
    StartupListResponse,
    StartupResponse,
    StartupUpdate,
)

router = APIRouter(prefix="/startups", tags=["Startups"])


@router.get("", response_model=StartupListResponse)
async def list_startups(
    use_case: ListStartups = Depends(startup_builder(ListStartups)),
):
    items, total = await use_case.execute()
    return StartupListResponse(
        items=[StartupResponse.model_validate(s) for s in items],
        total=total,
    )


@router.get("/{startup_id}", response_model=StartupResponse)
async def get_startup(
    startup_id: uuid.UUID,
    use_case: GetStartup = Depends(startup_builder(GetStartup)),
):
    startup = await use_case.execute(startup_id)
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
    use_case: CreateStartup = Depends(startup_builder(CreateStartup)),
):
    startup = Startup(**data.model_dump())
    created = await use_case.execute(startup)
    return StartupResponse.model_validate(created)


@router.patch("/{startup_id}", response_model=StartupResponse)
async def update_startup(
    startup_id: uuid.UUID,
    data: StartupUpdate,
    get_uc: GetStartup = Depends(startup_builder(GetStartup)),
    update_uc: UpdateStartup = Depends(startup_builder(UpdateStartup)),
):
    startup = await get_uc.execute(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    updated = await update_uc.execute(startup, data.model_dump(exclude_unset=True))
    return StartupResponse.model_validate(updated)


@router.delete("/{startup_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_startup(
    startup_id: uuid.UUID,
    get_uc: GetStartup = Depends(startup_builder(GetStartup)),
    delete_uc: DeleteStartup = Depends(startup_builder(DeleteStartup)),
):
    startup = await get_uc.execute(startup_id)
    if not startup:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Startup com id {startup_id} não encontrada",
        )
    await delete_uc.execute(startup)
