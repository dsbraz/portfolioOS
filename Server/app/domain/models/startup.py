from __future__ import annotations

import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    Numeric,
    String,
    Text,
    false,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.exceptions import ConflictError
from app.domain.models import Base
from app.domain.models.period import Period

if TYPE_CHECKING:
    from app.domain.models.board_meeting import BoardMeeting
    from app.domain.models.executive import Executive
    from app.domain.models.monthly_indicator import MonthlyIndicator
    from app.domain.models.monthly_indicator_token import MonthlyIndicatorToken


class StartupStatus(str, enum.Enum):
    HEALTHY = "saudavel"
    WARNING = "atencao"
    CRITICAL = "critico"


EXITED_STARTUP_HAS_NO_LINK = (
    "Esta startup deixou de ser acompanhada e não recebe mais indicadores por link."
)
EXITED_STARTUP_TAKES_NO_LATER_PERIOD = (
    "Esta startup deixou de ser acompanhada e não recebe indicadores de meses "
    "posteriores à saída."
)


class ExitType(str, enum.Enum):
    """How the fund left the startup. A write-off is an exit, not another flow."""

    SALE = "venda"
    IPO = "ipo"
    BUYBACK = "recompra"
    WRITE_OFF = "baixa"


class Startup(Base):
    __tablename__ = "startups"
    __table_args__ = (
        # Date and type travel together: one without the other is not an exit.
        CheckConstraint(
            "(exited_on IS NULL) = (exit_type IS NULL)",
            name="ck_startups_exit_complete",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    site: Mapped[str | None] = mapped_column(String(512), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[StartupStatus] = mapped_column(
        Enum(StartupStatus, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=StartupStatus.HEALTHY,
    )
    sector: Mapped[str] = mapped_column(String(255), nullable=False)
    investment_date: Mapped[date] = mapped_column(Date, nullable=False)
    equity_stake: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Opt-in: the monthly job e-mails the reporting link only where this is on.
    monthly_report_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    # The exit is a separate dimension from `status`, which stays a health signal.
    # `exited_on` set means the fund left: the startup stops being tracked from
    # that month, and its history stays readable.
    exited_on: Mapped[date | None] = mapped_column(Date, nullable=True)
    exit_type: Mapped[ExitType | None] = mapped_column(
        Enum(
            ExitType,
            name="exit_type",
            values_callable=lambda cls: [e.value for e in cls],
        ),
        nullable=True,
    )
    exit_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    monthly_indicators: Mapped[list["MonthlyIndicator"]] = relationship(
        "MonthlyIndicator", back_populates="startup", cascade="all, delete-orphan"
    )
    board_meetings: Mapped[list["BoardMeeting"]] = relationship(
        "BoardMeeting", back_populates="startup", cascade="all, delete-orphan"
    )
    executives: Mapped[list["Executive"]] = relationship(
        "Executive", back_populates="startup", cascade="all, delete-orphan"
    )
    monthly_indicator_tokens: Mapped[list["MonthlyIndicatorToken"]] = relationship(
        "MonthlyIndicatorToken", back_populates="startup", cascade="all, delete-orphan"
    )

    def ensure_accepts_reports(self) -> None:
        """An exited startup has no reporting link at all, old or new."""
        if self.exited_on is not None:
            raise ConflictError(EXITED_STARTUP_HAS_NO_LINK)

    def ensure_accepts_indicator(self, period: Period, *, through_link: bool) -> None:
        """Whether an indicator for `period` may still be stored.

        Through a link, never once the startup exited. By hand, up to the exit
        month: its numbers often arrive after the exit is recorded, and that
        history remains available even though monitoring has ended.
        """
        if self.exited_on is None:
            return
        if through_link:
            raise ConflictError(EXITED_STARTUP_HAS_NO_LINK)
        if period > self._exit_month():
            raise ConflictError(EXITED_STARTUP_TAKES_NO_LATER_PERIOD)

    def is_tracked_in(self, period: Period) -> bool:
        """Track from the investment month (inclusive) to the exit month (exclusive)."""
        investment_month = Period(
            year=self.investment_date.year, month=self.investment_date.month
        )
        if period < investment_month:
            return False
        return self.exited_on is None or period < self._exit_month()

    def receives_monthly_report_for(self, period: Period) -> bool:
        """Whether the monthly job may e-mail the reporting link for `period`.

        Only where the send is on, and never once the startup exited — it has no
        reporting link at all, so an e-mail would carry a link that answers 409.
        Nor for a month it is not tracked in, such as one before the investment.
        `monthly_report_enabled` is left as it was on exit, so undoing the exit
        restores the send exactly as it stood.
        """
        return (
            self.monthly_report_enabled
            and self.exited_on is None
            and self.is_tracked_in(period)
        )

    def _exit_month(self) -> Period:
        return Period(year=self.exited_on.year, month=self.exited_on.month)
