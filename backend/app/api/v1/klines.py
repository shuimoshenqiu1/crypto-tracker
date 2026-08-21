from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.crud.coin import get_coin_by_id
from app.crud.kline import get_klines, save_klines
from app.db.session import get_db
from app.models.user import User
from app.schemas.common import error_response, success_response
from app.services.binance import fetch_klines

router = APIRouter(tags=["klines"])

VALID_INTERVALS = {"1m", "5m", "15m", "1h", "4h", "1d"}


@router.get("/coins/{coin_id}/klines")
async def get_coin_klines(
    coin_id: str,
    interval: str = Query("1h"),
    start_time: int = Query(..., description="起始时间 Unix ms"),
    end_time: int = Query(..., description="结束时间 Unix ms"),
    limit: int = Query(500, ge=1, le=1500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    # Validate interval
    if interval not in VALID_INTERVALS:
        raise HTTPException(
            status_code=400,
            detail=error_response(40001, f"无效的 interval，允许值: {', '.join(sorted(VALID_INTERVALS))}"),
        )

    # Validate time range
    if start_time >= end_time:
        raise HTTPException(
            status_code=400,
            detail=error_response(40001, "start_time 必须小于 end_time"),
        )

    # Validate coin exists
    coin = await get_coin_by_id(db, coin_id)
    if coin is None:
        raise HTTPException(
            status_code=404,
            detail=error_response(40401, "币种不存在"),
        )

    # Validate binance_symbol
    if not coin.binance_symbol:
        raise HTTPException(
            status_code=404,
            detail=error_response(40401, "该币种无 Binance 交易对"),
        )

    binance_symbol = coin.binance_symbol

    # Try DB first
    db_klines = await get_klines(db, coin_id, interval, start_time, end_time, limit)

    # If DB has fewer than expected, fetch from Binance and save
    if len(db_klines) < limit:
        fetched = await fetch_klines(
            symbol=binance_symbol,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        if fetched:
            await save_klines(db, coin_id, binance_symbol, interval, fetched)
            # Re-query from DB for consistent response
            db_klines = await get_klines(db, coin_id, interval, start_time, end_time, limit)

    klines_data = [
        {
            "open_time": k.open_time,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume,
            "close_time": k.close_time,
            "quote_volume": k.quote_volume,
            "trades_count": k.trades_count,
        }
        for k in db_klines
    ]

    return success_response(
        data={
            "coin_id": coin_id,
            "symbol": binance_symbol,
            "interval": interval,
            "klines": klines_data,
        }
    )
