import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.deal import DealColumn
from app.domain.schemas.common import PaginatedResponse


class DealBase(BaseModel):
    company: str = Field(..., min_length=1, max_length=255)
    sector: str | None = Field(None, max_length=255)
    stage: str | None = Field(None, max_length=100)
    founders: str | None = None
    column: DealColumn = DealColumn.NEW
    notes: str | None = None
    next_step: str | None = None
    internal_owner: str | None = Field(None, max_length=255)


class DealCreate(DealBase):
    pass


class DealUpdate(BaseModel):
    company: str | None = Field(None, min_length=1, max_length=255)
    sector: str | None = Field(None, max_length=255)
    stage: str | None = Field(None, max_length=100)
    founders: str | None = None
    column: DealColumn | None = None
    notes: str | None = None
    next_step: str | None = None
    internal_owner: str | None = Field(None, max_length=255)


class DealMoveRequest(BaseModel):
    column: DealColumn
    position: int = 0


class DealResponse(DealBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    position: int
    created_at: datetime
    updated_at: datetime


class DealListResponse(PaginatedResponse[DealResponse]):
    pass
