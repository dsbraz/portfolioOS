import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.startup import ExitType, StartupStatus
from app.controllers.schemas.common import PaginatedResponse


class StartupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    site: str | None = Field(None, max_length=512)
    logo_url: str | None = Field(None, max_length=512)
    status: StartupStatus = StartupStatus.HEALTHY
    sector: str = Field(..., min_length=1, max_length=255)
    investment_date: date
    equity_stake: Decimal | None = Field(None, ge=0, le=100)
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
    equity_stake: Decimal | None = Field(None, ge=0, le=100)
    notes: str | None = None


class StartupExitRecord(BaseModel):
    exited_on: date
    exit_type: ExitType
    exit_notes: str | None = None


class StartupResponse(StartupBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    exited_on: date | None = None
    exit_type: ExitType | None = None
    exit_notes: str | None = None
    created_at: datetime
    updated_at: datetime


class StartupListResponse(PaginatedResponse[StartupResponse]):
    pass
