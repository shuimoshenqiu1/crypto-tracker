from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import BigInteger, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Coin(Base):
    __tablename__ = "coins"

    id: Mapped[str] = mapped_column(String(100), primary_key=True)  # CoinGecko slug
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    current_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    market_cap: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    market_cap_rank: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    price_change_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_change_pct_24h: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_volume: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    circulating_supply: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_supply: Mapped[float | None] = mapped_column(Float, nullable=True)
    ath: Mapped[float | None] = mapped_column(Float, nullable=True)
    ath_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    binance_symbol: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
