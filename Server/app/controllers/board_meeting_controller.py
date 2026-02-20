import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.application.board_meeting.create_board_meeting import CreateBoardMeeting
from app.application.board_meeting.delete_board_meeting import DeleteBoardMeeting
from app.application.board_meeting.get_board_meeting import GetBoardMeeting
from app.application.board_meeting.list_board_meetings import ListBoardMeetings
from app.application.board_meeting.update_board_meeting import UpdateBoardMeeting
from app.controllers.dependencies import board_meeting_builder, verify_startup_exists
from app.domain.models.board_meeting import BoardMeeting
from app.domain.schemas.board_meeting import (
    BoardMeetingCreate,
    BoardMeetingListResponse,
    BoardMeetingResponse,
    BoardMeetingUpdate,
)

router = APIRouter(prefix="/startups/{startup_id}/meetings", tags=["Board Meetings"])


@router.get("", response_model=BoardMeetingListResponse)
async def list_meetings(
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: ListBoardMeetings = Depends(board_meeting_builder(ListBoardMeetings)),
):
    items, total = await use_case.execute(startup_id)
    return BoardMeetingListResponse(
        items=[BoardMeetingResponse.model_validate(m) for m in items],
        total=total,
    )


@router.post(
    "", response_model=BoardMeetingResponse, status_code=status.HTTP_201_CREATED
)
async def create_meeting(
    data: BoardMeetingCreate,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: CreateBoardMeeting = Depends(board_meeting_builder(CreateBoardMeeting)),
):
    meeting = BoardMeeting(startup_id=startup_id, **data.model_dump())
    created = await use_case.execute(meeting)
    return BoardMeetingResponse.model_validate(created)


@router.get("/{meeting_id}", response_model=BoardMeetingResponse)
async def get_meeting(
    meeting_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: GetBoardMeeting = Depends(board_meeting_builder(GetBoardMeeting)),
):
    meeting = await use_case.execute(meeting_id)
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
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetBoardMeeting = Depends(board_meeting_builder(GetBoardMeeting)),
    update_uc: UpdateBoardMeeting = Depends(board_meeting_builder(UpdateBoardMeeting)),
):
    meeting = await get_uc.execute(meeting_id)
    if not meeting or meeting.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reunião com id {meeting_id} não encontrada",
        )
    updated = await update_uc.execute(meeting, data.model_dump(exclude_unset=True))
    return BoardMeetingResponse.model_validate(updated)


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: uuid.UUID,
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    get_uc: GetBoardMeeting = Depends(board_meeting_builder(GetBoardMeeting)),
    delete_uc: DeleteBoardMeeting = Depends(board_meeting_builder(DeleteBoardMeeting)),
):
    meeting = await get_uc.execute(meeting_id)
    if not meeting or meeting.startup_id != startup_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reunião com id {meeting_id} não encontrada",
        )
    await delete_uc.execute(meeting)
