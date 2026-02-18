import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.domain.schemas.common import PaginatedResponse, make_optional_model


class BoardMeetingBase(BaseModel):
    meeting_date: date
    participants: str | None = None
    summary: str | None = None
    attention_points: str | None = None
    next_steps: str | None = None


class BoardMeetingCreate(BoardMeetingBase):
    pass

BoardMeetingUpdate = make_optional_model(BoardMeetingBase, "BoardMeetingUpdate")


class BoardMeetingResponse(BoardMeetingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    startup_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class BoardMeetingListResponse(PaginatedResponse[BoardMeetingResponse]):
    pass
