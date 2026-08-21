from __future__ import annotations

import asyncio
import json
import logging
import time

import redis.asyncio as aioredis

from app.core.config import settings

logger = logging.getLogger(__name__)

BINANCE_WS_URL = "wss://stream.binance.com:9443/ws"
REDIS_PRICES_CHANNEL = "prices"
RECONNECT_DELAY = 5  # seconds


class BinanceWebSocketService:
    """Connects to Binance WebSocket for miniTicker updates and publishes to Redis."""

    def __init__(self) -> None:
        self._running = False
        self._redis: aioredis.Redis | None = None
        self._subscribed_symbols: set[str] = set()

    async def start(self) -> None:
        """Start the Binance WebSocket listener loop."""
        self._running = True
        self._redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

        while self._running:
            try:
                await self._connect_and_listen()
            except Exception as e:
                logger.error(f"Binance WS error: {e}")
            if self._running:
                logger.info(f"Binance WS reconnecting in {RECONNECT_DELAY}s...")
                await asyncio.sleep(RECONNECT_DELAY)

    async def stop(self) -> None:
        """Stop the service."""
        self._running = False
        if self._redis:
            await self._redis.aclose()
            self._redis = None

    async def _connect_and_listen(self) -> None:
        """Connect to Binance WS and listen for miniTicker messages."""
        try:
            import websockets
        except ImportError:
            logger.error("websockets package not installed, Binance WS disabled")
            self._running = False
            return

        # Subscribe to all miniTicker stream
        stream_url = f"{BINANCE_WS_URL}/!miniTicker@arr"

        async with websockets.connect(stream_url) as ws:
            logger.info("Connected to Binance WebSocket (all miniTicker)")
            while self._running:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=30)
                    data = json.loads(raw)

                    if isinstance(data, list):
                        # Array of miniTicker updates
                        for ticker in data:
                            await self._process_ticker(ticker)
                    elif isinstance(data, dict):
                        # Single ticker or response
                        if "e" in data and data["e"] == "24hrMiniTicker":
                            await self._process_ticker(data)

                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    await ws.ping()
                except Exception as e:
                    logger.error(f"Binance WS recv error: {e}")
                    break

    async def _process_ticker(self, ticker: dict) -> None:
        """Process a miniTicker message and publish to Redis."""
        symbol = ticker.get("s", "")  # e.g. "BTCUSDT"
        if not symbol:
            return

        price_data = {
            "symbol": symbol,
            "price": float(ticker.get("c", 0)),  # 'c' = current/close price
            "price_change_pct_24h": self._calc_pct_change(ticker),
            "volume_24h": float(ticker.get("q", 0)),  # quote volume
            "timestamp": int(time.time() * 1000),
        }

        if self._redis:
            try:
                # Cache price
                await self._redis.set(
                    f"price:{symbol}", json.dumps(price_data), ex=30
                )
                # Publish for broadcaster
                await self._redis.publish(
                    REDIS_PRICES_CHANNEL, json.dumps(price_data)
                )
            except Exception as e:
                logger.warning(f"Redis publish failed for {symbol}: {e}")

    @staticmethod
    def _calc_pct_change(ticker: dict) -> float:
        """Calculate 24h percentage change from open and close."""
        try:
            open_price = float(ticker.get("o", 0))
            close_price = float(ticker.get("c", 0))
            if open_price > 0:
                return round(((close_price - open_price) / open_price) * 100, 4)
        except (ValueError, ZeroDivisionError):
            pass
        return 0.0


# Global instance
binance_ws_service = BinanceWebSocketService()
