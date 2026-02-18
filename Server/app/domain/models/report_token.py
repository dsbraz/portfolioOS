import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models import Base


class ReportToken(Base):
    __tablename__ = "report_tokens"
    __table_args__ = (
        UniqueConstraint(
            "startup_id", "month", "year",
            name="uq_report_token_startup_month_year",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    token: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4, unique=True
    )
    startup_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("startups.id", ondelete="CASCADE"),
        nullable=False,
    )
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    year: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    startup: Mapped["Startup"] = relationship(
        "Startup", back_populates="report_tokens"
    )
