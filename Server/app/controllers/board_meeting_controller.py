import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.models.board_meeting import BoardMeeting
from app.domain.schemas.board_meeting import (
    BoardMeetingCreate,
    BoardMeetingListResponse,
    BoardMeetingResponse,
    BoardMeetingUpdate,
)
from app.repositories.board_meeting_repository import BoardMeetingRepository
from app.repositories.startup_repository import StartupRepository
from app.services.board_meeting_service import BoardMeetingService

router = APIRouter(prefix="/startups/{startup_id}/meetings", tags=["Board Meetings"])


def _get_service(session: AsyncSession = Depends(get_session)) -> BoardMeetingService:
    return BoardMeetingService(BoardMeetingRepository(session))


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


@router.get("", response_model=BoardMeetingListResponse)
async def list_meetings(
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: BoardMeetingService = Depends(_get_service),
):
    items, total = await service.list_meetings(startup_id)
    return BoardMeetingListResponse(
        items=[BoardMeetingResponse.model_validate(m) for m in items],
        total=total,
    )


@router.post(
    "", response_model=BoardMeetingResponse, status_code=status.HTTP_201_CREATED
)
async def create_meeting(
    data: BoardMeetingCreate,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: BoardMeetingService = Depends(_get_service),
):
    meeting = BoardMeeting(startup_id=startup_id, **data.model_dump())
    created = await service.create_meeting(meeting)
    return BoardMeetingResponse.model_validate(created)


@router.get("/{meeting_id}", response_model=BoardMeetingResponse)
async def get_meeting(
    meeting_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: BoardMeetingService = Depends(_get_service),
):
    meeting = await service.get_meeting(meeting_id)
    if not meeting or meeting.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reunião com id {meeting_id} não encontrada",
        )
    return BoardMeetingResponse.model_validate(meeting)


@router.patch("/{meeting_id}", response_model=BoardMeetingResponse)
async def update_meeting(
    meeting_id: uuid.UUID,
    data: BoardMeetingUpdate,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: BoardMeetingService = Depends(_get_service),
):
    meeting = await service.get_meeting(meeting_id)
    if not meeting or meeting.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reunião com id {meeting_id} não encontrada",
        )
    updated = await service.update_meeting(meeting, data.model_dump(exclude_unset=True))
    return BoardMeetingResponse.model_validate(updated)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(_verify_startup_exists),
    service: BoardMeetingService = Depends(_get_service),
):
    meeting = await service.get_meeting(meeting_id)
    if not meeting or meeting.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reunião com id {meeting_id} não encontrada",
        )
    await service.delete_meeting(meeting)
