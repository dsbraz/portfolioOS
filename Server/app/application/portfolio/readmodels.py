from dataclasses import dataclass
from decimal import Decimal

from app.domain.models.startup import Startup


@dataclass(frozen=True)
class HealthDistribution:
    healthy: int = 0
    warning: int = 0
    critical: int = 0


@dataclass(frozen=True)
class StartupSummary:
    startup: Startup
    total_revenue: Decimal | None = None
    cash_balance: Decimal | None = None
    ebitda_burn: Decimal | None = None
    headcount: int | None = None


@dataclass(frozen=True)
class PortfolioSummary:
    total_startups: int
    revenue: Decimal
    health: HealthDistribution
    monthly_report_pct: float
    routines_up_to_date_pct: float
    startups: list[StartupSummary]
