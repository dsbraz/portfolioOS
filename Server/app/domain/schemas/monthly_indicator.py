from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.common import PaginatedResponse

_MAX_MONEY = Decimal("9999999999999.99")
_MIN_MONEY = Decimal("-9999999999999.99")
_MAX_PCT = Decimal("99999.99")
# Bounds of the `Integer` column behind `headcount`: a larger value cannot be
# stored, so the API refuses it (422) instead of failing in the driver (500).
_MAX_HEADCOUNT = 2_147_483_647

# Declared once and shared by every schema that accepts indicator values, so a
# limit cannot drift between creating, editing and the investee's public form.
Month = Annotated[int, Field(ge=1, le=12)]
Year = Annotated[int, Field(ge=2000, le=2100)]
Money = Annotated[Decimal, Field(ge=_MIN_MONEY, le=_MAX_MONEY)]
Pct = Annotated[Decimal, Field(ge=0, le=_MAX_PCT)]
Headcount = Annotated[int, Field(ge=0, le=_MAX_HEADCOUNT)]


# --- Monthly Indicator schemas ---


class MonthlyIndicatorBase(BaseModel):
    month: Month
    year: Year
    total_revenue: Money | None = None
    recurring_revenue_pct: Pct | None = None
    gross_margin_pct: Pct | None = None
    cash_balance: Money | None = None
    headcount: Headcount | None = None
    ebitda_burn: Money | None = None
    achievements: str | None = None
    challenges: str | None = None
    comments: str | None = None


class MonthlyIndicatorCreate(MonthlyIndicatorBase):
    pass


class MonthlyIndicatorUpdate(BaseModel):
    # Optional to send, but never null: the period cannot be erased.
    month: Month = None
    year: Year = None
    total_revenue: Money | None = None
    recurring_revenue_pct: Pct | None = None
    gross_margin_pct: Pct | None = None
    cash_balance: Money | None = None
    headcount: Headcount | None = None
    ebitda_burn: Money | None = None
    achievements: str | None = None
    challenges: str | None = None
    comments: str | None = None


class MonthlyIndicatorResponse(MonthlyIndicatorBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    startup_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MonthlyIndicatorListResponse(PaginatedResponse[MonthlyIndicatorResponse]):
    pass


# --- Token schemas (private routes) ---


class MonthlyIndicatorTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    token: uuid.UUID
    startup_id: uuid.UUID
    month: int
    year: int
    created_at: datetime


class MonthlyIndicatorTokenCreate(BaseModel):
    month: Month
    year: Year


class MonthlyIndicatorTokenListResponse(
    PaginatedResponse[MonthlyIndicatorTokenResponse]
):
    pass


# --- Public form schemas (public routes) ---


class PublicIndicatorData(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_revenue: Decimal | None = None
    cash_balance: Decimal | None = None
    ebitda_burn: Decimal | None = None
    recurring_revenue_pct: Decimal | None = None
    gross_margin_pct: Decimal | None = None
    headcount: int | None = None
    achievements: str | None = None
    challenges: str | None = None


class PublicIndicatorForm(BaseModel):
    startup_name: str
    startup_logo_url: str | None
    month: int
    year: int
    existing_indicator: PublicIndicatorData | None = None


class PublicIndicatorSubmit(BaseModel):
    total_revenue: Money | None = None
    cash_balance: Money | None = None
    ebitda_burn: Money | None = None
    recurring_revenue_pct: Pct | None = None
    gross_margin_pct: Pct | None = None
    headcount: Headcount | None = None
    achievements: str | None = None
    challenges: str | None = None
