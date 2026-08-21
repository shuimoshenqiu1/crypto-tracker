from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)

COINGECKO_MARKETS_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
)

# Common Binance symbol mapping
_BINANCE_SYMBOL_MAP: dict[str, str] = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "BNB": "BNBUSDT",
    "SOL": "SOLUSDT",
    "XRP": "XRPUSDT",
    "DOGE": "DOGEUSDT",
    "ADA": "ADAUSDT",
    "AVAX": "AVAXUSDT",
    "DOT": "DOTUSDT",
    "LINK": "LINKUSDT",
    "MATIC": "MATICUSDT",
    "UNI": "UNIUSDT",
    "ATOM": "ATOMUSDT",
    "LTC": "LTCUSDT",
    "FIL": "FILUSDT",
    "APT": "APTUSDT",
    "ARB": "ARBUSDT",
    "OP": "OPUSDT",
    "NEAR": "NEARUSDT",
    "SHIB": "SHIBUSDT",
}


async def fetch_top_coins(limit: int = 100) -> list[dict]:
    """Fetch top coins by market cap from CoinGecko.

    Returns a list of dicts ready for upsert into the Coin model.
    Handles rate limiting (max 30 req/min for free tier).
    """
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": min(limit, 250),
        "page": 1,
        "sparkline": "false",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(COINGECKO_MARKETS_URL, params=params)
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:
                logger.warning("CoinGecko rate limit hit, backing off 60s")
                await asyncio.sleep(60)
                return []
            logger.error(f"CoinGecko API error: {e.response.status_code}")
            return []
        except httpx.RequestError as e:
            logger.error(f"CoinGecko request failed: {e}")
            return []

    data = response.json()
    coins = []
    for item in data:
        symbol_upper = item.get("symbol", "").upper()
        ath_date = None
        if item.get("ath_date"):
            try:
                ath_date = datetime.fromisoformat(
                    item["ath_date"].replace("Z", "+00:00")
                )
            except (ValueError, TypeError):
                pass

        coins.append(
            {
                "id": item["id"],
                "symbol": symbol_upper,
                "name": item.get("name", ""),
                "image_url": item.get("image"),
                "current_price": item.get("current_price"),
                "market_cap": item.get("market_cap"),
                "market_cap_rank": item.get("market_cap_rank"),
                "price_change_24h": item.get("price_change_24h"),
                "price_change_pct_24h": item.get("price_change_percentage_24h"),
                "total_volume": item.get("total_volume"),
                "circulating_supply": item.get("circulating_supply"),
                "max_supply": item.get("max_supply"),
                "ath": item.get("ath"),
                "ath_date": ath_date,
                "binance_symbol": _BINANCE_SYMBOL_MAP.get(symbol_upper),
                "updated_at": datetime.now(timezone.utc),
            }
        )

    return coins
