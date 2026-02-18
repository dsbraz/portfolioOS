from decimal import Decimal

from pydantic import BaseModel

from app.domain.schemas.startup import StartupResponse


class StartupMonitoringItem(BaseModel):
    startup: StartupResponse
    total_revenue: Decimal | None = None
    cash_balance: Decimal | None = None
    ebitda_burn: Decimal | None = None
    headcount: int | None = None


class HealthDistribution(BaseModel):
    healthy: int = 0
    warning: int = 0
    critical: int = 0


class MonitoringSummary(BaseModel):
    total_startups: int
    portfolio_revenue: Decimal
    portfolio_health: HealthDistribution
    monthly_report_pct: float
    routines_up_to_date_pct: float
    startups: list[StartupMonitoringItem]
