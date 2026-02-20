from decimal import Decimal
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int


class FinancialMetrics(BaseModel):
    total_revenue: Decimal | None = None
    cash_balance: Decimal | None = None
    ebitda_burn: Decimal | None = None
    headcount: int | None = None
