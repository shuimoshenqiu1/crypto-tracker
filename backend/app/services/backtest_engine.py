from __future__ import annotations

import asyncio
import logging
import math

import numpy as np

from app.services.binance import fetch_klines
from app.services.strategies import Signal
from app.services.strategies.bollinger import run as bollinger_run
from app.services.strategies.ma_cross import run as ma_cross_run
from app.services.strategies.rsi import run as rsi_run

logger = logging.getLogger(__name__)

STRATEGY_MAP = {
    "ma_cross": ma_cross_run,
    "rsi": rsi_run,
    "bollinger": bollinger_run,
}

# Interval to milliseconds mapping
INTERVAL_MS = {
    "1m": 60_000,
    "5m": 300_000,
    "15m": 900_000,
    "1h": 3_600_000,
    "4h": 14_400_000,
    "1d": 86_400_000,
}


async def _fetch_all_klines(
    symbol: str, interval: str, start_time: int, end_time: int
) -> list[dict]:
    """Fetch all klines in range, paginating if necessary (Binance max 1000 per request)."""
    all_klines: list[dict] = []
    current_start = start_time
    limit = 1000

    while current_start < end_time:
        batch = await fetch_klines(
            symbol=symbol,
            interval=interval,
            start_time=current_start,
            end_time=end_time,
            limit=limit,
        )
        if not batch:
            break
        all_klines.extend(batch)
        # Move start past last candle
        last_close_time = batch[-1]["close_time"]
        current_start = last_close_time + 1
        if len(batch) < limit:
            break
        # Small delay to avoid rate limiting
        await asyncio.sleep(0.1)

    return all_klines


def _calculate_metrics(
    signals: list[Signal],
    prices: list[float],
    times: list[int],
    interval: str,
) -> dict:
    """Calculate backtest performance metrics from signals."""
    interval_ms = INTERVAL_MS.get(interval, 3_600_000)
    interval_hours = interval_ms / 3_600_000

    trades: list[dict] = []
    equity_curve: list[dict] = []
    initial_capital = 10000.0
    capital = initial_capital
    position_open = False
    entry_price = 0.0
    entry_time = 0
    entry_idx = 0

    winning_trades = 0
    losing_trades = 0
    gross_profit = 0.0
    gross_loss = 0.0
    holding_hours_total = 0.0

    # Build equity curve starting point
    equity_curve.append({"time": times[0], "value": initial_capital})

    for signal in signals:
        idx = signal.index
        if idx >= len(prices):
            continue
        price = prices[idx]
        time_ms = times[idx]

        if signal.type == "buy" and not position_open:
            position_open = True
            entry_price = price
            entry_time = time_ms
            entry_idx = idx
            trades.append({
                "type": "buy",
                "price": price,
                "time": time_ms,
                "quantity": 1.0,
            })
        elif signal.type == "sell" and position_open:
            position_open = False
            pnl_pct = (price - entry_price) / entry_price
            capital *= 1 + pnl_pct
            holding_hours = (idx - entry_idx) * interval_hours

            holding_hours_total += holding_hours

            if pnl_pct > 0:
                winning_trades += 1
                gross_profit += pnl_pct * (capital / (1 + pnl_pct))
            else:
                losing_trades += 1
                gross_loss += abs(pnl_pct) * (capital / (1 + pnl_pct))

            trades.append({
                "type": "sell",
                "price": price,
                "time": time_ms,
                "quantity": 1.0,
            })
            equity_curve.append({"time": time_ms, "value": round(capital, 2)})

    # If position still open at end, close at last price
    if position_open and len(prices) > 0:
        last_price = prices[-1]
        last_time = times[-1]
        pnl_pct = (last_price - entry_price) / entry_price
        capital *= 1 + pnl_pct
        holding_hours = (len(prices) - 1 - entry_idx) * interval_hours
        holding_hours_total += holding_hours

        if pnl_pct > 0:
            winning_trades += 1
            gross_profit += pnl_pct * (capital / (1 + pnl_pct))
        else:
            losing_trades += 1
            gross_loss += abs(pnl_pct) * (capital / (1 + pnl_pct))

        trades.append({
            "type": "sell",
            "price": last_price,
            "time": last_time,
            "quantity": 1.0,
        })
        equity_curve.append({"time": last_time, "value": round(capital, 2)})

    # Calculate metrics
    total_trades = (winning_trades + losing_trades)
    total_return_pct = ((capital - initial_capital) / initial_capital) * 100

    # Annualized return
    total_hours = len(prices) * interval_hours
    total_years = total_hours / (365 * 24) if total_hours > 0 else 1
    if total_return_pct > -100:
        annualized_return_pct = ((1 + total_return_pct / 100) ** (1 / total_years) - 1) * 100
    else:
        annualized_return_pct = -100.0

    # Max drawdown from equity curve
    max_drawdown_pct = 0.0
    if equity_curve:
        equity_values = [p["value"] for p in equity_curve]
        peak = equity_values[0]
        for val in equity_values:
            if val > peak:
                peak = val
            drawdown = (val - peak) / peak * 100
            if drawdown < max_drawdown_pct:
                max_drawdown_pct = drawdown

    # Sharpe ratio: (mean_return - 0) / std_return * sqrt(365*24) for hourly
    # Calculate per-period returns from equity curve
    sharpe_ratio = 0.0
    if len(equity_curve) > 1:
        eq_vals = np.array([p["value"] for p in equity_curve], dtype=np.float64)
        returns = np.diff(eq_vals) / eq_vals[:-1]
        if len(returns) > 1 and np.std(returns) > 0:
            periods_per_year = (365 * 24) / interval_hours
            sharpe_ratio = float(
                np.mean(returns) / np.std(returns) * math.sqrt(periods_per_year)
            )

    # Win rate
    win_rate_pct = (winning_trades / total_trades * 100) if total_trades > 0 else 0.0

    # Profit factor
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else float("inf")
    if math.isinf(profit_factor):
        profit_factor = 99.99  # cap for JSON serialization

    # Average holding hours
    avg_holding_hours = (holding_hours_total / total_trades) if total_trades > 0 else 0.0

    return {
        "total_return_pct": round(total_return_pct, 2),
        "annualized_return_pct": round(annualized_return_pct, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "total_trades": total_trades,
        "win_rate_pct": round(win_rate_pct, 2),
        "profit_factor": round(profit_factor, 2),
        "avg_holding_hours": round(avg_holding_hours, 1),
        "trades": trades,
        "equity_curve": equity_curve,
    }


async def run_backtest(
    coin_id: str,
    strategy_name: str,
    params: dict,
    interval: str,
    start_time: int,
    end_time: int,
) -> dict:
    """Run a backtest for a given coin and strategy.

    Args:
        coin_id: CoinGecko slug (used to derive Binance symbol)
        strategy_name: One of 'ma_cross', 'rsi', 'bollinger'
        params: Strategy-specific parameters
        interval: K-line interval ('1m','5m','15m','1h','4h','1d')
        start_time: Start time in Unix ms
        end_time: End time in Unix ms

    Returns:
        Dict with performance metrics, trades, and equity curve.

    Raises:
        ValueError: If strategy is unknown or data is insufficient.
    """
    if strategy_name not in STRATEGY_MAP:
        raise ValueError(f"Unknown strategy: {strategy_name}")

    # Derive Binance symbol from coin_id
    # Common mapping: bitcoin -> BTCUSDT, ethereum -> ETHUSDT
    # We need to fetch from DB ideally, but for the engine we expect caller
    # to pass a coin_id that maps. Use uppercase + USDT as fallback.
    symbol_map = {
        "bitcoin": "BTCUSDT",
        "ethereum": "ETHUSDT",
        "solana": "SOLUSDT",
        "binancecoin": "BNBUSDT",
        "ripple": "XRPUSDT",
        "cardano": "ADAUSDT",
        "dogecoin": "DOGEUSDT",
        "polkadot": "DOTUSDT",
        "avalanche-2": "AVAXUSDT",
        "chainlink": "LINKUSDT",
    }
    symbol = symbol_map.get(coin_id, coin_id.upper().replace("-", "") + "USDT")

    # Fetch klines from Binance
    klines = await _fetch_all_klines(symbol, interval, start_time, end_time)
    if not klines:
        raise ValueError("历史数据不足，无法完成回测")

    if len(klines) < 30:
        raise ValueError("历史数据不足，需要至少30根K线")

    # Extract close prices and times
    prices = [k["close"] for k in klines]
    times = [k["open_time"] for k in klines]

    # Run strategy
    strategy_fn = STRATEGY_MAP[strategy_name]
    signals = strategy_fn(prices, params)

    # Calculate metrics
    result = _calculate_metrics(signals, prices, times, interval)
    return result
