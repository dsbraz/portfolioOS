"""Value objects para o agregado de monitoramento do portfolio.

Dataclasses imutáveis que representam resumos computados
sem mapeamento direto a tabela no banco.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.domain.models.startup import Startup


@dataclass(frozen=True)
class HealthDistribution:
    healthy: int = 0
    warning: int = 0
    critical: int = 0


@dataclass(frozen=True)
class StartupMonitoringItem:
    startup: Startup
    total_revenue: Decimal | None = None
    cash_balance: Decimal | None = None
    ebitda_burn: Decimal | None = None
    headcount: int | None = None


@dataclass(frozen=True)
class PortfolioSummary:
    total_startups: int
    portfolio_revenue: Decimal
    portfolio_health: HealthDistribution
    monthly_report_pct: float
    routines_up_to_date_pct: float
    startups: list[StartupMonitoringItem]
