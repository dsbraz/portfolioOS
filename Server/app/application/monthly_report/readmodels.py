import uuid
from dataclasses import dataclass

from app.domain.models.monthly_report_dispatch import DispatchKind
from app.domain.models.period import Period


@dataclass(frozen=True)
class MonthlyReportRecipient:
    executive_id: uuid.UUID
    name: str
    email: str


@dataclass(frozen=True)
class MonthlyReportPlan:
    """What one startup's monthly send needs, read once and committed.

    Plain values, not ORM rows: each recipient is then sent in a transaction of
    its own, and a plan must not depend on the session that built it.
    """

    startup_id: uuid.UUID
    startup_name: str
    period: Period
    kind: DispatchKind
    form_token: uuid.UUID
    recipients: tuple[MonthlyReportRecipient, ...]
