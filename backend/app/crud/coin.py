from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coin import Coin


async def get_coins(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 20,
    sort_by: str = "market_cap_rank",
    sort_order: str = "asc",
    search: str | None = None,
) -> tuple[list[Coin], int]:
    """Get paginated coin list with sorting and search."""
    allowed_sort_fields = {
        "market_cap_rank",
        "price_change_pct_24h",
        "total_volume",
        "name",
    }
    if sort_by not in allowed_sort_fields:
        sort_by = "market_cap_rank"

    query = select(Coin)
    count_query = select(func.count()).select_from(Coin)

    if search:
        search_filter = or_(
            Coin.name.ilike(f"%{search}%"),
            Coin.symbol.ilike(f"%{search}%"),
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Sorting
    sort_column = getattr(Coin, sort_by)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc().nulls_last())
    else:
        query = query.order_by(sort_column.asc().nulls_last())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    items = list(result.scalars().all())

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    return items, total


async def get_coin_by_id(db: AsyncSession, coin_id: str) -> Coin | None:
    """Get a single coin by its CoinGecko slug."""
    result = await db.execute(select(Coin).where(Coin.id == coin_id))
    return result.scalar_one_or_none()


async def upsert_coins(db: AsyncSession, coins_data: list[dict]) -> None:
    """Bulk upsert coins from CoinGecko data."""
    if not coins_data:
        return

    stmt = pg_insert(Coin).values(coins_data)
    stmt = stmt.on_conflict_do_update(
        index_elements=["id"],
        set_={
            "symbol": stmt.excluded.symbol,
            "name": stmt.excluded.name,
            "image_url": stmt.excluded.image_url,
            "current_price": stmt.excluded.current_price,
            "market_cap": stmt.excluded.market_cap,
            "market_cap_rank": stmt.excluded.market_cap_rank,
            "price_change_24h": stmt.excluded.price_change_24h,
            "price_change_pct_24h": stmt.excluded.price_change_pct_24h,
            "total_volume": stmt.excluded.total_volume,
            "circulating_supply": stmt.excluded.circulating_supply,
            "max_supply": stmt.excluded.max_supply,
            "ath": stmt.excluded.ath,
            "ath_date": stmt.excluded.ath_date,
            "binance_symbol": stmt.excluded.binance_symbol,
            "updated_at": datetime.now(timezone.utc),
        },
    )
    await db.execute(stmt)
    await db.commit()
