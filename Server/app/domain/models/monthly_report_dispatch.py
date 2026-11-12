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
    """One automatic e-mail of the reporting link: who, which period, which send.

    The unique key is what makes the monthly job safe to run twice: a send that
    already went out is found, not repeated.
    """

    __tablename__ = "monthly_report_dispatches"
    __table_args__ = (
        UniqueConstraint(
            "startup_id",
            "executive_id",
            "month",
            "year",
            "kind",
            name="uq_monthly_report_dispatch_recipient_period_kind",
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
    # Kept when the executive is deleted: the history says the mail went out.
    executive_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("executives.id", ondelete="SET NULL"),
        nullable=True,
    )
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
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
