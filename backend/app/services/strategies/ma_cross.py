from __future__ import annotations

import numpy as np

from app.services.strategies import Signal


def run(prices: list[float], params: dict) -> list[Signal]:
    """MA crossover strategy.

    Buy when short MA crosses above long MA, sell when crosses below.

    Params:
        short_period: int (default 7)
        long_period: int (default 25)
    """
    short_period = params.get("short_period", 7)
    long_period = params.get("long_period", 25)

    if len(prices) < long_period:
        return []

    arr = np.array(prices, dtype=np.float64)

    # Compute simple moving averages
    short_ma = np.convolve(arr, np.ones(short_period) / short_period, mode="valid")
    long_ma = np.convolve(arr, np.ones(long_period) / long_period, mode="valid")

    # Align: short_ma starts at index (short_period - 1), long_ma at (long_period - 1)
    # We need to align them to the same price index
    offset = long_period - short_period
    short_ma_aligned = short_ma[offset:]  # trim short_ma to align with long_ma

    # Both now have length = len(prices) - long_period + 1
    # The actual price index for position i in these arrays is: long_period - 1 + i
    signals: list[Signal] = []
    for i in range(1, len(long_ma)):
        price_idx = long_period - 1 + i
        prev_short = short_ma_aligned[i - 1]
        prev_long = long_ma[i - 1]
        curr_short = short_ma_aligned[i]
        curr_long = long_ma[i]

        # Golden cross: short crosses above long
        if prev_short <= prev_long and curr_short > curr_long:
            signals.append(Signal(type="buy", index=price_idx))
        # Death cross: short crosses below long
        elif prev_short >= prev_long and curr_short < curr_long:
            signals.append(Signal(type="sell", index=price_idx))

    return signals
