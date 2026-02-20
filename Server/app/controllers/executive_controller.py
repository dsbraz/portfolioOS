import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.executive.create_executive import CreateExecutive
from app.application.executive.delete_executive import DeleteExecutive
from app.application.executive.get_executive import GetExecutive
from app.application.executive.list_executives import ListExecutives
from app.application.executive.update_executive import UpdateExecutive
from app.controllers.dependencies import executive_builder, verify_startup_exists
from app.domain.models.executive import Executive
from app.domain.schemas.executive import (
    ExecutiveCreate,
    ExecutiveListResponse,
    ExecutiveResponse,
    ExecutiveUpdate,
)

router = APIRouter(prefix="/startups/{startup_id}/executives", tags=["Executives"])


@router.get("", response_model=ExecutiveListResponse)
async def list_executives(
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: ListExecutives = Depends(executive_builder(ListExecutives)),
):
    items, total = await use_case.execute(startup_id)
    return ExecutiveListResponse(
        items=[ExecutiveResponse.model_validate(e) for e in items],
        total=total,
    )


@router.post(
    "", response_model=ExecutiveResponse, status_code=status.HTTP_201_CREATED
)
async def create_executive(
    data: ExecutiveCreate,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: CreateExecutive = Depends(executive_builder(CreateExecutive)),
):
    executive = Executive(startup_id=startup_id, **data.model_dump())
    created = await use_case.execute(executive)
    return ExecutiveResponse.model_validate(created)


@router.get("/{executive_id}", response_model=ExecutiveResponse)
async def get_executive(
    executive_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: GetExecutive = Depends(executive_builder(GetExecutive)),
):
    executive = await use_case.execute(executive_id)
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
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetExecutive = Depends(executive_builder(GetExecutive)),
    update_uc: UpdateExecutive = Depends(executive_builder(UpdateExecutive)),
):
    executive = await get_uc.execute(executive_id)
    if not executive or executive.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executivo com id {executive_id} não encontrado",
        )
    updated = await update_uc.execute(executive, data.model_dump(exclude_unset=True))
    return ExecutiveResponse.model_validate(updated)


@router.delete("/{executive_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_executive(
    executive_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetExecutive = Depends(executive_builder(GetExecutive)),
    delete_uc: DeleteExecutive = Depends(executive_builder(DeleteExecutive)),
):
    executive = await get_uc.execute(executive_id)
    if not executive or executive.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Executivo com id {executive_id} não encontrado",
        )
    await delete_uc.execute(executive)
