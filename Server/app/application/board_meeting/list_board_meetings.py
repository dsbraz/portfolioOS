import uuid

from app.domain.models.board_meeting import BoardMeeting
from app.repositories.board_meeting_repository import BoardMeetingRepository


class ListBoardMeetings:
    def __init__(self, repository: BoardMeetingRepository) -> None:
        self._repository = repository

    async def execute(self, startup_id: uuid.UUID) -> tuple[list[BoardMeeting], int]:
        return await self._repository.get_all_by_startup(startup_id)
