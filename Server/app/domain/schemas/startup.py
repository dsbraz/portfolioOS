import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.startup import StartupStatus
from app.domain.schemas.common import PaginatedResponse


class StartupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    site: str | None = Field(None, max_length=512)
    logo_url: str | None = Field(None, max_length=512)
    status: StartupStatus = StartupStatus.HEALTHY
    sector: str = Field(..., min_length=1, max_length=255)
    investment_date: date
    notes: str | None = None


class StartupCreate(StartupBase):
    pass


class StartupUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    site: str | None = Field(None, max_length=512)
    logo_url: str | None = Field(None, max_length=512)
    status: StartupStatus | None = None
    sector: str | None = Field(None, min_length=1, max_length=255)
    investment_date: date | None = None
    notes: str | None = None


class StartupResponse(StartupBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class StartupListResponse(PaginatedResponse[StartupResponse]):
    pass
