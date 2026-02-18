import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models import Base


class StartupStatus(str, enum.Enum):
    HEALTHY = "saudavel"
    WARNING = "atencao"
    CRITICAL = "critico"


class Startup(Base):
    __tablename__ = "startups"

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
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
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
