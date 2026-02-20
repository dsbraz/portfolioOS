from app.domain.models.board_meeting import BoardMeeting
from app.repositories.board_meeting_repository import BoardMeetingRepository


class CreateBoardMeeting:
    def __init__(self, repository: BoardMeetingRepository) -> None:
        self._repository = repository

    async def execute(self, meeting: BoardMeeting) -> BoardMeeting:
        return await self._repository.create(meeting)
