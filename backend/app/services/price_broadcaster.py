from __future__ import annotations

import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.core.config import settings
from app.ws.manager import manager

logger = logging.getLogger(__name__)

REDIS_PRICES_CHANNEL = "prices"


class PriceBroadcaster:
    """Subscribes to Redis pubsub 'prices' channel and broadcasts to WebSocket clients."""

    def __init__(self) -> None:
        self._running = False
        self._redis: aioredis.Redis | None = None

    async def start(self) -> None:
        """Start listening to Redis pubsub and broadcasting."""
        self._running = True
        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

        while self._running:
            try:
                await self._subscribe_and_broadcast()
            except Exception as e:
                logger.error(f"PriceBroadcaster error: {e}")
                if self._running:
                    await asyncio.sleep(2)

    async def stop(self) -> None:
        """Stop the broadcaster."""
        self._running = False
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def _subscribe_and_broadcast(self) -> None:
        """Subscribe to Redis and forward messages to WebSocket manager."""
        if not self._redis:
            return

        pubsub = self._redis.pubsub()
        await pubsub.subscribe(REDIS_PRICES_CHANNEL)

        try:
            while self._running:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    try:
                        price_data = json.loads(message["data"])
                        symbol = price_data.get("symbol", "")
                        if symbol:
                            await manager.broadcast_price(symbol, price_data)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Invalid price message: {e}")
                else:
                    # Small sleep to prevent busy-wait
                    await asyncio.sleep(0.01)
        finally:
            await pubsub.unsubscribe(REDIS_PRICES_CHANNEL)
            await pubsub.aclose()


# Global instance
price_broadcaster = PriceBroadcaster()
