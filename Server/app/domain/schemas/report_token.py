from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ReportTokenCreate(BaseModel):
    month: int = Field(..., ge=1, le=12)
    year: int = Field(..., ge=2000, le=2100)


class ReportTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    token: uuid.UUID
    startup_id: uuid.UUID
    month: int
    year: int
    created_at: datetime


class ReportTokenListResponse(BaseModel):
    items: list[ReportTokenResponse]
    total: int


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


class ReportFormContext(BaseModel):
    startup_name: str
    startup_logo_url: str | None
    month: int
    year: int
    existing_indicator: PublicIndicatorData | None = None


class PublicReportSubmit(BaseModel):
    total_revenue: Decimal | None = None
    cash_balance: Decimal | None = None
    ebitda_burn: Decimal | None = None
    recurring_revenue_pct: Decimal | None = None
    gross_margin_pct: Decimal | None = None
    headcount: int | None = None
    achievements: str | None = None
    challenges: str | None = None
