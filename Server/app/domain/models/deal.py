import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.models import Base


class DealColumn(str, enum.Enum):
    NEW = "novo"
    TALKING = "conversando"
    ANALYZING = "analisando"
    COMMITTEE = "comite"
    INVESTED = "investido"
    ARCHIVED = "arquivado"


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    sector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    founders: Mapped[str | None] = mapped_column(Text, nullable=True)
    column: Mapped[DealColumn] = mapped_column(
        Enum(DealColumn, values_callable=lambda cls: [e.value for e in cls]),
        nullable=False,
        default=DealColumn.NEW,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_step: Mapped[str | None] = mapped_column(Text, nullable=True)
    internal_owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
