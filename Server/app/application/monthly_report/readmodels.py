import enum
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

    Plain values, not ORM rows: each recipient is then claimed and recorded in
    transactions of its own, and a plan must not depend on the session that
    built it.
    """

    startup_id: uuid.UUID
    startup_name: str
    period: Period
    kind: DispatchKind
    form_token: uuid.UUID
    recipients: tuple[MonthlyReportRecipient, ...]


class MonthlyReportSkip(str, enum.Enum):
    """Why a startup with the monthly send on gets nothing this run.

    Told apart because they mean opposite things: one is the job working, the
    other a gap the operator has to close in the registry.
    """

    ALREADY_REPORTED = "already_reported"
    NO_RECIPIENTS = "no_recipients"
