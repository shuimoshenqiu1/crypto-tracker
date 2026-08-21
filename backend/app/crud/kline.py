from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kline import Kline


async def get_klines(
    db: AsyncSession,
    coin_id: str,
    interval: str,
    start_time: int,
    end_time: int,
    limit: int = 500,
) -> list[Kline]:
    """Query klines from DB for a given coin, interval, and time range."""
    query = (
        select(Kline)
        .where(
            Kline.coin_id == coin_id,
            Kline.interval == interval,
            Kline.open_time >= start_time,
            Kline.open_time <= end_time,
        )
        .order_by(Kline.open_time.asc())
        .limit(limit)
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def save_klines(
    db: AsyncSession,
    coin_id: str,
    symbol: str,
    interval: str,
    klines_data: list[dict],
) -> None:
    """Bulk insert klines, skipping duplicates on (symbol, interval, open_time)."""
    if not klines_data:
        return

    rows = [
        {
            "coin_id": coin_id,
            "symbol": symbol,
            "interval": interval,
            "open_time": k["open_time"],
            "open": k["open"],
            "high": k["high"],
            "low": k["low"],
            "close": k["close"],
            "volume": k["volume"],
            "close_time": k["close_time"],
            "quote_volume": k.get("quote_volume"),
            "trades_count": k.get("trades_count"),
        }
        for k in klines_data
    ]

    stmt = pg_insert(Kline).values(rows)
    stmt = stmt.on_conflict_do_nothing(
        constraint="uq_klines_symbol_interval_open_time"
    )
    await db.execute(stmt)
    await db.commit()
