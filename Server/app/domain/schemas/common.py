from copy import deepcopy
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


def make_optional_model(
    base: type[BaseModel],
    name: str,
) -> type[BaseModel]:
    """Create an all-optional version of a Pydantic model, preserving field constraints."""
    fields = {}
    annotations = {}
    for field_name, field_info in base.model_fields.items():
        new_field = deepcopy(field_info)
        new_field.default = None
        new_field.annotation = field_info.annotation | None
        annotations[field_name] = field_info.annotation | None
        fields[field_name] = new_field
    ns = {"__annotations__": annotations, **fields}
    model = type(name, (BaseModel,), ns)
    model.model_rebuild()
    return model
