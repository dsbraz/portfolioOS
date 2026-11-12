import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.models.startup import StartupStatus
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
    monthly_report_enabled: bool = False


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
    # Optional in a PATCH but never null: the column is NOT NULL, and an
    # explicit null must be a 422, not a database error. The default is not
    # validated, so omitting the field still leaves it out of the update.
    monthly_report_enabled: bool = None  # type: ignore[assignment]


class StartupResponse(StartupBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class StartupListResponse(PaginatedResponse[StartupResponse]):
    pass
