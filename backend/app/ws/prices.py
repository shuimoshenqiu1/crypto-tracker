from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_access_token
from app.ws.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()

HEARTBEAT_INTERVAL = 30  # seconds
HEARTBEAT_TIMEOUT = 60  # seconds without pong -> disconnect


@router.websocket("/ws/prices")
async def ws_prices(websocket: WebSocket, token: str = Query(...)) -> None:
    # Authenticate via query param JWT
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=4001, reason="Token 无效或已过期")
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=4001, reason="Token 无效")
        return

    await manager.connect(websocket, user_id)

    # Heartbeat task
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
                # Check if pong was received within timeout
                now = asyncio.get_event_loop().time()
                if now - last_pong > HEARTBEAT_TIMEOUT:
                    logger.info(f"WS heartbeat timeout for user {user_id}")
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
                await websocket.send_text(
                    json.dumps({"type": "error", "code": 40001, "message": "Invalid JSON"})
                )
                continue

            msg_type = msg.get("type") or msg.get("action")

            if msg_type == "pong":
                last_pong = asyncio.get_event_loop().time()

            elif msg_type == "subscribe":
                symbols = msg.get("symbols", [])
                if isinstance(symbols, list) and symbols:
                    await manager.subscribe(websocket, symbols)
                    await websocket.send_text(
                        json.dumps({"type": "subscribed", "symbols": symbols})
                    )

            elif msg_type == "unsubscribe":
                symbols = msg.get("symbols", [])
                if isinstance(symbols, list) and symbols:
                    await manager.unsubscribe(websocket, symbols)
                    await websocket.send_text(
                        json.dumps({"type": "unsubscribed", "symbols": symbols})
                    )

            else:
                await websocket.send_text(
                    json.dumps({"type": "error", "code": 40001, "message": f"Unknown action: {msg_type}"})
                )

    except WebSocketDisconnect:
        logger.info(f"WS disconnected for user {user_id}")
    except Exception as e:
        logger.error(f"WS error for user {user_id}: {e}")
    finally:
        if heartbeat_task:
            heartbeat_task.cancel()
        await manager.disconnect(websocket, user_id)
