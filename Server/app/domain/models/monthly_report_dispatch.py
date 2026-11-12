from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models import Base


class DispatchKind(str, enum.Enum):
    INITIAL = "initial"
    REMINDER = "reminder"


class MonthlyReportDispatch(Base):
    """One automatic e-mail of the reporting link: which address, period and send.

    The unique key is what makes the monthly job safe to run twice: a send that
    already went out is found, not repeated. It is keyed by address, not by
    executive: two executives sharing an inbox get one e-mail, and a changed
    address is a new recipient that has not seen the request.

    The job claims the row before the e-mail leaves and records the outcome
    after, so a row is in one of three states: delivered (`sent_at`), failed
    (`error`, retried by the next run), or unconfirmed (neither — the outcome
    was never recorded, so the mail may or may not have left; never resent
    automatically).
    """

    __tablename__ = "monthly_report_dispatches"
    __table_args__ = (
        UniqueConstraint(
            "startup_id",
            "recipient_email",
            "month",
            "year",
            "kind",
            name="uq_monthly_report_dispatch_address_period_kind",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    startup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("startups.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Who it was addressed to, for the history; the address is the identity.
    # Kept when the executive is deleted: the history says the mail went out.
    executive_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executives.id", ondelete="SET NULL"),
        nullable=True,
    )
    # Trimmed and lower-cased by the plan, so the unique key compares addresses.
    recipient_email: Mapped[str] = mapped_column(String(255), nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    kind: Mapped[DispatchKind] = mapped_column(
        Enum(
            DispatchKind,
            name="monthlyreportdispatchkind",
            values_callable=lambda cls: [e.value for e in cls],
        ),
        nullable=False,
    )
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Both set explicitly by the job, never by `onupdate`: a retry that fails
    # with the same error changes no column, and would keep the old date.
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    @property
    def delivered(self) -> bool:
        return self.sent_at is not None

    @property
    def failed(self) -> bool:
        return self.error is not None
