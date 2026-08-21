from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    coin_id: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("coins.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    condition_type: Mapped[str] = mapped_column(
        String(30), nullable=False
    )  # price_above | price_below | pct_change_above | pct_change_below
    threshold: Mapped[float] = mapped_column(Numeric(24, 8), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    is_repeating: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    cooldown_secs: Mapped[int] = mapped_column(Integer, nullable=False, default=3600)
    last_triggered: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
