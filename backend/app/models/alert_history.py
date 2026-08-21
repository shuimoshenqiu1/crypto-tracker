from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AlertHistory(Base):
    __tablename__ = "alert_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    alert_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coin_id: Mapped[str] = mapped_column(String(100), nullable=False)
    coin_symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    condition_type: Mapped[str] = mapped_column(String(30), nullable=False)
    threshold: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    trigger_price: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
