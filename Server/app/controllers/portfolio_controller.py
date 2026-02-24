from fastapi import APIRouter, Depends

from app.application.portfolio.get_portfolio_summary import GetPortfolioSummary
from app.controllers.dependencies import portfolio_builder
from app.domain.schemas.portfolio import (
    HealthDistribution,
    PortfolioSummary,
    StartupSummary,
)
from app.domain.schemas.startup import StartupResponse

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    use_case: GetPortfolioSummary = Depends(portfolio_builder(GetPortfolioSummary)),
):
    summary = await use_case.execute()
    return PortfolioSummary(
        total_startups=summary.total_startups,
        revenue=summary.revenue,
        health=HealthDistribution(
            healthy=summary.health.healthy,
            warning=summary.health.warning,
            critical=summary.health.critical,
        ),
        monthly_report_pct=summary.monthly_report_pct,
        routines_up_to_date_pct=summary.routines_up_to_date_pct,
        startups=[
            StartupSummary(
                startup=StartupResponse.model_validate(item.startup),
                total_revenue=item.total_revenue,
                cash_balance=item.cash_balance,
                ebitda_burn=item.ebitda_burn,
                headcount=item.headcount,
            )
            for item in summary.startups
        ],
    )
