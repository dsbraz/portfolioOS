import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.controllers.schemas.common import PaginatedResponse
from app.domain.models.monthly_report_dispatch import DispatchKind


class MonthlyReportDispatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    startup_id: uuid.UUID
    executive_id: uuid.UUID | None
    recipient_email: str
    month: int
    year: int
    kind: DispatchKind
    error: str | None
    sent_at: datetime


class MonthlyReportDispatchListResponse(
    PaginatedResponse[MonthlyReportDispatchResponse]
):
    pass
