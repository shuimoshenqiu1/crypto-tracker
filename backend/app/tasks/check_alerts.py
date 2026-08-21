from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone

import redis

from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

CONDITION_TYPES = {"price_above", "price_below", "pct_change_above", "pct_change_below"}


def _build_trigger_message(
    coin_symbol: str, condition_type: str, threshold: float, trigger_price: float
) -> str:
    """Build a human-readable trigger message."""
    th_str = f"${threshold:,.2f}" if condition_type.startswith("price_") else f"{threshold}%"

    if condition_type == "price_above":
        return f"{coin_symbol} 价格突破 {th_str}，当前价格 ${trigger_price:,.2f}"
    elif condition_type == "price_below":
        return f"{coin_symbol} 价格跌破 {th_str}，当前价格 ${trigger_price:,.2f}"
    elif condition_type == "pct_change_above":
        return f"{coin_symbol} 24h涨幅超过 {th_str}，当前价格 ${trigger_price:,.2f}"
    elif condition_type == "pct_change_below":
        return f"{coin_symbol} 24h跌幅超过 {th_str}，当前价格 ${trigger_price:,.2f}"
    return f"{coin_symbol} 告警触发，当前价格 ${trigger_price:,.2f}"


def _check_condition(
    condition_type: str, threshold: float, current_price: float, pct_change_24h: float | None
) -> bool:
    """Check if an alert condition is met."""
    if condition_type == "price_above":
        return current_price > threshold
    elif condition_type == "price_below":
        return current_price < threshold
    elif condition_type == "pct_change_above":
        if pct_change_24h is None:
            return False
        return pct_change_24h > threshold
    elif condition_type == "pct_change_below":
        if pct_change_24h is None:
            return False
        return pct_change_24h < -threshold
    return False


async def _check_alerts_async() -> int:
    """Check all active alerts against current prices."""
    import os

    from sqlalchemy import select, update
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.core.config import settings
    from app.models.alert import Alert
    from app.models.alert_history import AlertHistory
    from app.models.coin import Coin

    engine = create_async_engine(
        settings.DATABASE_URL, echo=False, pool_size=2, max_overflow=0
    )
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Connect to Redis synchronously for price reads
    redis_url = os.environ.get("REDIS_URL", settings.REDIS_URL)
    redis_client = redis.from_url(redis_url, decode_responses=True)

    triggered_count = 0
    now = datetime.now(timezone.utc)

    try:
        async with session_factory() as db:
            # Get all active alerts with coin info
            stmt = (
                select(Alert, Coin.symbol, Coin.binance_symbol)
                .join(Coin, Alert.coin_id == Coin.id)
                .where(Alert.is_active == True)  # noqa: E712
            )
            result = await db.execute(stmt)
            rows = result.all()

            for alert, coin_symbol, binance_symbol in rows:
                if not binance_symbol:
                    continue

                # Check cooldown
                if alert.last_triggered:
                    elapsed = (now - alert.last_triggered).total_seconds()
                    if elapsed < alert.cooldown_secs:
                        continue

                # Get current price from Redis
                price_key = f"price:{binance_symbol}"
                price_data_str = redis_client.get(price_key)
                if not price_data_str:
                    continue

                try:
                    price_data = json.loads(price_data_str)
                    current_price = float(price_data.get("price", 0))
                    pct_change_24h = price_data.get("price_change_pct_24h")
                    if pct_change_24h is not None:
                        pct_change_24h = float(pct_change_24h)
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue

                if current_price <= 0:
                    continue

                # Check condition
                if not _check_condition(
                    alert.condition_type, float(alert.threshold), current_price, pct_change_24h
                ):
                    continue

                # Condition met - trigger alert
                message = _build_trigger_message(
                    coin_symbol, alert.condition_type, float(alert.threshold), current_price
                )

                # Create history record
                history = AlertHistory(
                    alert_id=alert.id,
                    user_id=alert.user_id,
                    coin_id=alert.coin_id,
                    coin_symbol=coin_symbol,
                    condition_type=alert.condition_type,
                    threshold=float(alert.threshold),
                    trigger_price=current_price,
                    message=message,
                    triggered_at=now,
                )
                db.add(history)

                # Update alert last_triggered
                alert.last_triggered = now

                # If non-repeating, deactivate
                if not alert.is_repeating:
                    alert.is_active = False

                alert.updated_at = now

                # Publish to Redis 'alerts' channel for WS broadcast
                alert_event = {
                    "user_id": str(alert.user_id),
                    "type": "alert_triggered",
                    "data": {
                        "alert_id": str(alert.id),
                        "coin_id": alert.coin_id,
                        "coin_symbol": coin_symbol,
                        "condition_type": alert.condition_type,
                        "threshold": float(alert.threshold),
                        "trigger_price": current_price,
                        "message": message,
                        "triggered_at": int(now.timestamp() * 1000),
                    },
                }
                redis_client.publish("alerts", json.dumps(alert_event))

                triggered_count += 1

            await db.commit()

    finally:
        redis_client.close()
        await engine.dispose()

    return triggered_count


@celery_app.task(
    name="app.tasks.check_alerts.check_alert_rules",
    soft_time_limit=30,
    time_limit=45,
)
def check_alert_rules() -> str:
    """Celery task: check all active alert rules against current prices."""
    triggered = asyncio.run(_check_alerts_async())
    if triggered > 0:
        logger.info(f"Triggered {triggered} alerts")
    return f"Checked alerts, triggered {triggered}"
