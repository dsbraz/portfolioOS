from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.domain.schemas.common import PaginatedResponse

_MAX_MONEY = Decimal("9999999999999.99")
_MIN_MONEY = Decimal("-9999999999999.99")
_MAX_PCT = Decimal("99999.99")


# --- Monthly Indicator schemas ---


class MonthlyIndicatorBase(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)
    total_revenue: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    recurring_revenue_pct: Decimal | None = Field(None, ge=0, le=_MAX_PCT)
    gross_margin_pct: Decimal | None = Field(None, ge=0, le=_MAX_PCT)
    cash_balance: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    headcount: int | None = Field(None, ge=0)
    ebitda_burn: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    achievements: str | None = None
    challenges: str | None = None
    comments: str | None = None


class MonthlyIndicatorCreate(MonthlyIndicatorBase):
    pass


class MonthlyIndicatorUpdate(BaseModel):
    month: int | None = Field(None, ge=1, le=12)
    year: int | None = Field(None, ge=2000, le=2100)
    total_revenue: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    recurring_revenue_pct: Decimal | None = Field(None, ge=0, le=_MAX_PCT)
    gross_margin_pct: Decimal | None = Field(None, ge=0, le=_MAX_PCT)
    cash_balance: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    headcount: int | None = Field(None, ge=0)
    ebitda_burn: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
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
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)


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
    total_revenue: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    cash_balance: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    ebitda_burn: Decimal | None = Field(None, ge=_MIN_MONEY, le=_MAX_MONEY)
    recurring_revenue_pct: Decimal | None = Field(None, ge=0, le=_MAX_PCT)
    gross_margin_pct: Decimal | None = Field(None, ge=0, le=_MAX_PCT)
    headcount: int | None = Field(None, ge=0)
    achievements: str | None = None
    challenges: str | None = None
