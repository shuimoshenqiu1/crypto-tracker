from __future__ import annotations

import uuid

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coin import Coin
from app.models.watchlist import Watchlist


async def get_watchlist(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """Get user watchlist joined with coin data, ordered by sort_order."""
    stmt = (
        select(
            Watchlist.coin_id,
            Coin.symbol,
            Coin.name,
            Coin.image_url,
            Coin.current_price,
            Coin.price_change_pct_24h,
            Watchlist.sort_order,
            Watchlist.added_at,
        )
        .join(Coin, Watchlist.coin_id == Coin.id)
        .where(Watchlist.user_id == user_id)
        .order_by(Watchlist.sort_order.asc(), Watchlist.added_at.asc())
    )
    result = await db.execute(stmt)
    rows = result.all()
    return [
        {
            "coin_id": row.coin_id,
            "symbol": row.symbol,
            "name": row.name,
            "image_url": row.image_url,
            "current_price": row.current_price,
            "price_change_pct_24h": row.price_change_pct_24h,
            "sort_order": row.sort_order,
            "added_at": int(row.added_at.timestamp() * 1000),
        }
        for row in rows
    ]


async def count_watchlist(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Count total watchlist items for user."""
    stmt = select(func.count()).select_from(Watchlist).where(Watchlist.user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar_one()


async def add_to_watchlist(
    db: AsyncSession, user_id: uuid.UUID, coin_id: str, sort_order: int
) -> Watchlist:
    """Add a coin to user watchlist."""
    item = Watchlist(user_id=user_id, coin_id=coin_id, sort_order=sort_order)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


async def remove_from_watchlist(
    db: AsyncSession, user_id: uuid.UUID, coin_id: str
) -> bool:
    """Remove a coin from user watchlist. Returns True if deleted."""
    stmt = (
        delete(Watchlist)
        .where(Watchlist.user_id == user_id, Watchlist.coin_id == coin_id)
        .returning(Watchlist.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def get_watchlist_item(
    db: AsyncSession, user_id: uuid.UUID, coin_id: str
) -> Watchlist | None:
    """Get a single watchlist item."""
    stmt = select(Watchlist).where(
        Watchlist.user_id == user_id, Watchlist.coin_id == coin_id
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
