from __future__ import annotations

import numpy as np

from app.services.strategies import Signal


def run(prices: list[float], params: dict) -> list[Signal]:
    """RSI strategy.

    Buy when RSI drops below oversold level, sell when RSI rises above overbought level.

    Params:
        period: int (default 14)
        oversold: float (default 30)
        overbought: float (default 70)
    """
    period = params.get("period", 14)
    oversold = params.get("oversold", 30.0)
    overbought = params.get("overbought", 70.0)

    if len(prices) < period + 1:
        return []

    arr = np.array(prices, dtype=np.float64)
    deltas = np.diff(arr)

    # Calculate RSI using exponential moving average (Wilder's smoothing)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)

    # First average: simple average of first `period` values
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])

    rsi_values: list[float] = []

    # RSI for the first period-th delta (index = period in prices)
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100.0 - 100.0 / (1.0 + rs))

    # Calculate remaining RSI values using Wilder's smoothing
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100.0 - 100.0 / (1.0 + rs))

    # rsi_values[i] corresponds to prices[period + i]
    signals: list[Signal] = []
    for i in range(1, len(rsi_values)):
        price_idx = period + i
        prev_rsi = rsi_values[i - 1]
        curr_rsi = rsi_values[i]

        # Buy when RSI crosses below oversold
        if prev_rsi >= oversold and curr_rsi < oversold:
            signals.append(Signal(type="buy", index=price_idx))
        # Sell when RSI crosses above overbought
        elif prev_rsi <= overbought and curr_rsi > overbought:
            signals.append(Signal(type="sell", index=price_idx))

    return signals
