from __future__ import annotations

import asyncio
import json
import logging

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

REDIS_ALERTS_CHANNEL = "alerts"


class AlertBroadcaster:
    """Subscribes to Redis pubsub 'alerts' channel and pushes to WS /ws/alerts connected users."""

    def __init__(self) -> None:
        self._running = False
        self._redis: aioredis.Redis | None = None

    async def start(self) -> None:
        """Start listening to Redis pubsub and broadcasting alerts."""
        self._running = True
        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

        while self._running:
            try:
                await self._subscribe_and_broadcast()
            except Exception as e:
                logger.error(f"AlertBroadcaster error: {e}")
                if self._running:
                    await asyncio.sleep(2)

    async def stop(self) -> None:
        """Stop the broadcaster."""
        self._running = False
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def _subscribe_and_broadcast(self) -> None:
        """Subscribe to Redis alerts channel and forward to WebSocket clients."""
        if not self._redis:
            return

        pubsub = self._redis.pubsub()
        await pubsub.subscribe(REDIS_ALERTS_CHANNEL)

        try:
            while self._running:
                message = await pubsub.get_message(
                    ignore_subscribe_messages=True, timeout=1.0
                )
                if message and message["type"] == "message":
                    try:
                        alert_event = json.loads(message["data"])
                        user_id = alert_event.get("user_id")
                        if user_id:
                            # Import here to avoid circular imports
                            from app.ws.alerts import alert_manager

                            ws_message = {
                                "type": alert_event.get("type", "alert_triggered"),
                                "data": alert_event.get("data", {}),
                            }
                            await alert_manager.send_to_user(user_id, ws_message)
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.warning(f"Invalid alert message: {e}")
                else:
                    await asyncio.sleep(0.01)
        finally:
            await pubsub.unsubscribe(REDIS_ALERTS_CHANNEL)
            await pubsub.aclose()


# Global instance
alert_broadcaster = AlertBroadcaster()
