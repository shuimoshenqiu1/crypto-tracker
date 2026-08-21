from __future__ import annotations

import asyncio
import json
import logging
from collections import defaultdict

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and symbol subscriptions."""

    def __init__(self) -> None:
        # user_id -> list of WebSocket connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)
        # websocket id -> set of subscribed symbols
        self._subscriptions: dict[int, set[str]] = defaultdict(set)
        # symbol -> set of websocket ids subscribed
        self._symbol_subscribers: dict[str, set[int]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            self._connections[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        ws_id = id(websocket)
        async with self._lock:
            # Remove from user connections
            if user_id in self._connections:
                self._connections[user_id] = [
                    ws for ws in self._connections[user_id] if ws is not websocket
                ]
                if not self._connections[user_id]:
                    del self._connections[user_id]
            # Remove subscriptions
            subscribed_symbols = self._subscriptions.pop(ws_id, set())
            for symbol in subscribed_symbols:
                self._symbol_subscribers[symbol].discard(ws_id)
                if not self._symbol_subscribers[symbol]:
                    del self._symbol_subscribers[symbol]

    async def subscribe(self, websocket: WebSocket, symbols: list[str]) -> None:
        ws_id = id(websocket)
        async with self._lock:
            for symbol in symbols:
                upper_symbol = symbol.upper()
                self._subscriptions[ws_id].add(upper_symbol)
                self._symbol_subscribers[upper_symbol].add(ws_id)

    async def unsubscribe(self, websocket: WebSocket, symbols: list[str]) -> None:
        ws_id = id(websocket)
        async with self._lock:
            for symbol in symbols:
                upper_symbol = symbol.upper()
                self._subscriptions[ws_id].discard(upper_symbol)
                self._symbol_subscribers[upper_symbol].discard(ws_id)
                if not self._symbol_subscribers[upper_symbol]:
                    del self._symbol_subscribers[upper_symbol]

    async def broadcast_price(self, symbol: str, price_data: dict) -> None:
        """Broadcast price update to all WebSocket connections subscribed to this symbol."""
        upper_symbol = symbol.upper()
        async with self._lock:
            subscriber_ids = set(self._symbol_subscribers.get(upper_symbol, set()))

        if not subscriber_ids:
            return

        message = json.dumps({"type": "price_update", "data": price_data})

        # Find all websockets matching subscriber_ids
        websockets_to_send: list[WebSocket] = []
        async with self._lock:
            for conns in self._connections.values():
                for ws in conns:
                    if id(ws) in subscriber_ids:
                        websockets_to_send.append(ws)

        for ws in websockets_to_send:
            try:
                await ws.send_text(message)
            except Exception:
                logger.debug(f"Failed to send price to ws {id(ws)}")

    def get_all_subscribed_symbols(self) -> set[str]:
        """Get all symbols currently subscribed by any connection."""
        symbols: set[str] = set()
        for sym_set in self._subscriptions.values():
            symbols.update(sym_set)
        return symbols


# Global manager instance
manager = ConnectionManager()
