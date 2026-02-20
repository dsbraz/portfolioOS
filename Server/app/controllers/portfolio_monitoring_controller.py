from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.domain.schemas.portfolio_monitoring import (
    HealthDistribution,
    MonitoringSummary,
    StartupMonitoringItem,
)
from app.domain.schemas.startup import StartupResponse
from app.repositories.portfolio_monitoring_repository import (
    PortfolioMonitoringRepository,
)
from app.repositories.startup_repository import StartupRepository
from app.use_cases.portfolio_monitoring.get_portfolio_summary import (
    GetPortfolioSummary,
)

router = APIRouter(prefix="/portfolio-monitoring", tags=["Portfolio Monitoring"])


def _get_use_case(
    session: AsyncSession = Depends(get_session),
) -> GetPortfolioSummary:
    return GetPortfolioSummary(
        StartupRepository(session),
        PortfolioMonitoringRepository(session),
    )


@router.get("/summary", response_model=MonitoringSummary)
async def get_monitoring_summary(
    use_case: GetPortfolioSummary = Depends(_get_use_case),
):
    summary = await use_case.execute()
    return MonitoringSummary(
        total_startups=summary.total_startups,
        portfolio_revenue=summary.portfolio_revenue,
        portfolio_health=HealthDistribution(
            healthy=summary.portfolio_health.healthy,
            warning=summary.portfolio_health.warning,
            critical=summary.portfolio_health.critical,
        ),
        monthly_report_pct=summary.monthly_report_pct,
        routines_up_to_date_pct=summary.routines_up_to_date_pct,
        startups=[
            StartupMonitoringItem(
                startup=StartupResponse.model_validate(item.startup),
                total_revenue=item.total_revenue,
                cash_balance=item.cash_balance,
                ebitda_burn=item.ebitda_burn,
                headcount=item.headcount,
            )
            for item in summary.startups
        ],
    )
