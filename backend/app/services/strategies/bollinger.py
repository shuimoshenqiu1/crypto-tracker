from __future__ import annotations

import numpy as np

from app.services.strategies import Signal


def run(prices: list[float], params: dict) -> list[Signal]:
    """Bollinger Bands strategy.

    Buy when price touches/crosses below the lower band,
    sell when price touches/crosses above the upper band.

    Params:
        period: int (default 20)
        std_dev: float (default 2.0)
    """
    period = params.get("period", 20)
    std_dev = params.get("std_dev", 2.0)

    if len(prices) < period:
        return []

    arr = np.array(prices, dtype=np.float64)

    signals: list[Signal] = []

    for i in range(period - 1, len(arr)):
        window = arr[i - period + 1 : i + 1]
        sma = np.mean(window)
        std = np.std(window, ddof=0)
        upper_band = sma + std_dev * std
        lower_band = sma - std_dev * std

        price = arr[i]

        if i == period - 1:
            # First point, no previous state to compare
            continue

        prev_window = arr[i - period : i]
        prev_sma = np.mean(prev_window)
        prev_std = np.std(prev_window, ddof=0)
        prev_upper = prev_sma + std_dev * prev_std
        prev_lower = prev_sma - std_dev * prev_std
        prev_price = arr[i - 1]

        # Buy: price crosses below lower band
        if prev_price >= prev_lower and price < lower_band:
            signals.append(Signal(type="buy", index=i))
        # Sell: price crosses above upper band
        elif prev_price <= prev_upper and price > upper_band:
            signals.append(Signal(type="sell", index=i))

    return signals
