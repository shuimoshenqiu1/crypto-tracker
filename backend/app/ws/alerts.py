from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token

logger = logging.getLogger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL = 30
HEARTBEAT_TIMEOUT = 60


class AlertConnectionManager:
    """Manages WebSocket connections for alert notifications per user."""

    def __init__(self) -> None:
        # user_id -> list of WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = []
            self._connections[user_id].append(websocket)

    async def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id] = [
                    ws for ws in self._connections[user_id] if ws is not websocket
                ]
                if not self._connections[user_id]:
                    del self._connections[user_id]

    async def send_to_user(self, user_id: str, message: dict) -> None:
        """Send a message to all connections of a specific user."""
        async with self._lock:
            connections = list(self._connections.get(user_id, []))

        if not connections:
            return

        text = json.dumps(message)
        for ws in connections:
            try:
                await ws.send_text(text)
            except Exception:
                logger.debug(f"Failed to send alert to user {user_id}")


# Global instance
alert_manager = AlertConnectionManager()


@router.websocket("/ws/alerts")
async def ws_alerts(websocket: WebSocket, token: str = Query(...)) -> None:
    # Authenticate via query param JWT
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Token 无效或已过期")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Token 无效")
        return

    await alert_manager.connect(websocket, user_id)

    last_pong = asyncio.get_event_loop().time()
    heartbeat_task: asyncio.Task | None = None

    async def heartbeat() -> None:
        nonlocal last_pong
        try:
            while True:
                await asyncio.sleep(HEARTBEAT_INTERVAL)
                try:
                    await websocket.send_text(json.dumps({"type": "ping"}))
                except Exception:
                    break
                now = asyncio.get_event_loop().time()
                if now - last_pong > HEARTBEAT_TIMEOUT:
                    logger.info(f"WS alerts heartbeat timeout for user {user_id}")
                    await websocket.close(code=4002, reason="Heartbeat timeout")
                    break
        except asyncio.CancelledError:
            pass

    try:
        heartbeat_task = asyncio.create_task(heartbeat())

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = msg.get("type")
            if msg_type == "pong":
                last_pong = asyncio.get_event_loop().time()

    except WebSocketDisconnect:
        logger.info(f"WS alerts disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WS alerts error for user {user_id}: {e}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        await alert_manager.disconnect(websocket, user_id)
