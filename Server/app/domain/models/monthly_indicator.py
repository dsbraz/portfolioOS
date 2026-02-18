import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models import Base


class MonthlyIndicator(Base):
    __tablename__ = "monthly_indicators"
    __table_args__ = (
        UniqueConstraint("startup_id", "month", "year", name="uq_indicator_startup_month_year"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    startup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("startups.id", ondelete="CASCADE"),
        nullable=False,
    )
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    total_revenue: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    recurring_revenue_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    gross_margin_pct: Mapped[Decimal | None] = mapped_column(Numeric(7, 2), nullable=True)
    cash_balance: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    headcount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ebitda_burn: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    achievements: Mapped[str | None] = mapped_column(Text, nullable=True)
    challenges: Mapped[str | None] = mapped_column(Text, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    startup: Mapped["Startup"] = relationship("Startup", back_populates="monthly_indicators")
