from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"


async def fetch_klines(
    symbol: str,
    interval: str,
    start_time: int,
    end_time: int,
    limit: int = 500,
) -> list[dict]:
    """Fetch K-line (candlestick) data from Binance REST API.

    Args:
        symbol: Binance trading pair (e.g. 'BTCUSDT')
        interval: Candle interval ('1m','5m','15m','1h','4h','1d')
        start_time: Start time in Unix ms
        end_time: End time in Unix ms
        limit: Max number of candles (max 1000 per Binance)

    Returns:
        List of kline dicts with keys:
        open_time, open, high, low, close, volume, close_time, quote_volume, trades_count
    """
    params = {
        "symbol": symbol,
        "interval": interval,
        "startTime": start_time,
        "endTime": end_time,
        "limit": min(limit, 1000),
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(BINANCE_KLINES_URL, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(
                f"Binance klines API error: {e.response.status_code} for {symbol}"
            )
            return []
        except httpx.RequestError as e:
            logger.error(f"Binance klines request failed: {e}")
            return []

    raw_klines = response.json()
    result: list[dict] = []

    for kline in raw_klines:
        # Binance kline array format:
        # [0] Open time, [1] Open, [2] High, [3] Low, [4] Close,
        # [5] Volume, [6] Close time, [7] Quote asset volume,
        # [8] Number of trades, [9] Taker buy base vol,
        # [10] Taker buy quote vol, [11] Ignore
        result.append(
            {
                "open_time": int(kline[0]),
                "open": float(kline[1]),
                "high": float(kline[2]),
                "low": float(kline[3]),
                "close": float(kline[4]),
                "volume": float(kline[5]),
                "close_time": int(kline[6]),
                "quote_volume": float(kline[7]),
                "trades_count": int(kline[8]),
            }
        )

    return result
