from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Signal:
    """A trading signal produced by a strategy."""

    type: str  # 'buy' | 'sell'
    index: int  # index in the price array
