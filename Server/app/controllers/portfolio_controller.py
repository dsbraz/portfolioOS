from fastapi import APIRouter, Depends, HTTPException, Query, status

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
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=1),
    use_case: GetPortfolioSummary = Depends(portfolio_builder(GetPortfolioSummary)),
):
    try:
        summary = await use_case.execute(month=month, year=year)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return PortfolioSummary(
        total_startups=summary.total_startups,
        revenue=summary.revenue,
        revenue_variation_pct=summary.revenue_variation_pct,
        revenue_variation_direction=summary.revenue_variation_direction,
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
