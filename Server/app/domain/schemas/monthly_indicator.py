import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.common import PaginatedResponse, make_optional_model


class MonthlyIndicatorBase(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)
    total_revenue: Decimal | None = None
    recurring_revenue_pct: Decimal | None = None
    gross_margin_pct: Decimal | None = None
    cash_balance: Decimal | None = None
    headcount: int | None = None
    ebitda_burn: Decimal | None = None
    achievements: str | None = None
    challenges: str | None = None
    comments: str | None = None


class MonthlyIndicatorCreate(MonthlyIndicatorBase):
    pass


MonthlyIndicatorUpdate = make_optional_model(MonthlyIndicatorBase, "MonthlyIndicatorUpdate")


class MonthlyIndicatorResponse(MonthlyIndicatorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    startup_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MonthlyIndicatorListResponse(PaginatedResponse[MonthlyIndicatorResponse]):
    pass
