from __future__ import annotations

import asyncio
import logging

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


async def _sync_coins_async() -> int:
    """Fetch coins from CoinGecko and upsert into DB."""
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.config import settings
    from app.services.coingecko import fetch_top_coins
    from app.crud.coin import upsert_coins

    # Create a short-lived engine for this task execution
    engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_size=2, max_overflow=0)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        coins_data = await fetch_top_coins(limit=100)
        if not coins_data:
            logger.warning("No coins fetched from CoinGecko")
            return 0

        async with session_factory() as session:
            await upsert_coins(session, coins_data)

        return len(coins_data)
    finally:
        await engine.dispose()


@celery_app.task(
    name="app.tasks.sync_coins.sync_coin_metadata",
    soft_time_limit=60,
    time_limit=90,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def sync_coin_metadata() -> str:
    """Celery task: sync coin metadata from CoinGecko."""
    count = asyncio.run(_sync_coins_async())
    logger.info(f"Synced {count} coins from CoinGecko")
    return f"Synced {count} coins"
