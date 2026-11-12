import uuid

from fastapi import APIRouter, Depends

from app.application.monthly_report.list_monthly_report_dispatches import (
    ListMonthlyReportDispatches,
)
from app.controllers.dependencies import (
    monthly_report_dispatch_builder,
    verify_startup_exists,
)
from app.controllers.schemas.monthly_report import (
    MonthlyReportDispatchListResponse,
    MonthlyReportDispatchResponse,
)

# Read-only: the sends themselves come from scripts/dispatch_monthly_report.py,
# run by the scheduled job, never from a request.
router = APIRouter(tags=["Monthly Report"])


@router.get(
    "/startups/{startup_id}/monthly-report-dispatches",
    response_model=MonthlyReportDispatchListResponse,
)
async def list_monthly_report_dispatches(
    startup_id: uuid.UUID = Depends(verify_startup_exists),
    use_case: ListMonthlyReportDispatches = Depends(
        monthly_report_dispatch_builder(ListMonthlyReportDispatches)
    ),
):
    items, total = await use_case.execute(startup_id)
    return MonthlyReportDispatchListResponse(
        items=[MonthlyReportDispatchResponse.model_validate(d) for d in items],
        total=total,
    )
