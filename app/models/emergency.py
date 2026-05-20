from datetime import datetime, timezone
from sqlalchemy import String, Text, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.core.database import Base


class EmergencyType(str, enum.Enum):
    bus        = "bus"
    helicopter = "helicopter"


class EmergencyStatus(str, enum.Enum):
    new        = "new"
    accepted   = "accepted"
    dispatched = "dispatched"
    arrived    = "arrived"
    closed     = "closed"


class EmergencyCall(Base):
    __tablename__ = "emergency_calls"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    # Явно указываем foreign_keys чтобы не было конфликта с dispatcher_id
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])  # noqa: F821

    type: Mapped[EmergencyType] = mapped_column(SAEnum(EmergencyType), nullable=False)
    status: Mapped[EmergencyStatus] = mapped_column(
        SAEnum(EmergencyStatus), default=EmergencyStatus.new, nullable=False
    )

    address: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    dispatcher_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    dispatcher_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    dispatcher: Mapped["User | None"] = relationship("User", foreign_keys=[dispatcher_id])  # noqa: F821

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<EmergencyCall id={self.id} type={self.type} status={self.status}>"
