import uuid

from app.domain.models.board_meeting import BoardMeeting
from app.repositories.board_meeting_repository import BoardMeetingRepository


class GetBoardMeeting:
    def __init__(self, repository: BoardMeetingRepository) -> None:
        self._repository = repository

    async def execute(self, meeting_id: uuid.UUID) -> BoardMeeting | None:
        return await self._repository.get_by_id(meeting_id)
