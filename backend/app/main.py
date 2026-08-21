from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.v1.auth import router as auth_router
from app.api.v1.coins import router as coins_router
from app.api.v1.klines import router as klines_router
from app.api.v1.watchlist import router as watchlist_router
from app.api.v1.alerts import router as alerts_router
from app.api.v1.backtest import router as backtest_router
from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.models import User, Coin, Kline, Watchlist, Alert, AlertHistory, BacktestJob  # noqa: F401 -- ensure models registered
from app.schemas.common import error_response
from app.ws.prices import router as ws_router
from app.ws.alerts import router as ws_alerts_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background services
    from app.services.binance_ws import binance_ws_service
    from app.services.price_broadcaster import price_broadcaster
    from app.services.alert_broadcaster import alert_broadcaster

    binance_task = asyncio.create_task(binance_ws_service.start())
    broadcaster_task = asyncio.create_task(price_broadcaster.start())
    alert_broadcaster_task = asyncio.create_task(alert_broadcaster.start())

    yield

    # Shutdown: stop background services
    await binance_ws_service.stop()
    await price_broadcaster.stop()
    await alert_broadcaster.stop()
    binance_task.cancel()
    broadcaster_task.cancel()
    alert_broadcaster_task.cancel()

    from app.services.cache import close_redis
    await close_redis()
    await engine.dispose()


app = FastAPI(
    title="CryptoTracker API",
    version=settings.APP_VERSION,
    redirect_slashes=False,
    lifespan=lifespan,
)


# --- Exception handlers ---


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    messages = []
    for err in exc.errors():
        loc = " -> ".join(str(x) for x in err["loc"] if x != "body")
        messages.append(f"{loc}: {err['msg']}")
    return JSONResponse(
        status_code=422,
        content=error_response(42201, "; ".join(messages)),
    )


# --- Health endpoint ---


@app.get("/api/v1/health")
async def health_check() -> dict:
    return {
        "code": 0,
        "data": {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "services": {
                "database": "connected",
                "redis": "connected",
                "celery": "active",
            },
            "timestamp": int(time.time() * 1000),
        },
        "message": "",
    }


# --- Routers ---

app.include_router(auth_router, prefix="/api/v1")
app.include_router(coins_router, prefix="/api/v1")
app.include_router(klines_router, prefix="/api/v1")
app.include_router(watchlist_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(backtest_router, prefix="/api/v1")
app.include_router(ws_router)
app.include_router(ws_alerts_router)
