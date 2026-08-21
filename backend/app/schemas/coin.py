from __future__ import annotations

from pydantic import BaseModel


class CoinListItem(BaseModel):
    """Schema for coin list response (API-SPEC 2.1)."""

    id: str
    symbol: str
    name: str
    image_url: str | None = None
    current_price: float | None = None
    market_cap: int | None = None
    market_cap_rank: int | None = None
    price_change_pct_24h: float | None = None
    total_volume: int | None = None
    binance_symbol: str | None = None

    class Config:
        from_attributes = True


class CoinDetail(BaseModel):
    """Schema for coin detail response (API-SPEC 2.2)."""

    id: str
    symbol: str
    name: str
    image_url: str | None = None
    current_price: float | None = None
    market_cap: int | None = None
    market_cap_rank: int | None = None
    price_change_24h: float | None = None
    price_change_pct_24h: float | None = None
    total_volume: int | None = None
    circulating_supply: float | None = None
    max_supply: float | None = None
    ath: float | None = None
    ath_date: int | None = None  # Unix ms
    binance_symbol: str | None = None
    updated_at: int | None = None  # Unix ms

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, coin) -> CoinDetail:
        """Convert Coin model to CoinDetail, transforming dates to Unix ms."""
        ath_date_ms = int(coin.ath_date.timestamp() * 1000) if coin.ath_date else None
        updated_at_ms = int(coin.updated_at.timestamp() * 1000) if coin.updated_at else None
        return cls(
            id=coin.id,
            symbol=coin.symbol,
            name=coin.name,
            image_url=coin.image_url,
            current_price=coin.current_price,
            market_cap=coin.market_cap,
            market_cap_rank=coin.market_cap_rank,
            price_change_24h=coin.price_change_24h,
            price_change_pct_24h=coin.price_change_pct_24h,
            total_volume=coin.total_volume,
            circulating_supply=coin.circulating_supply,
            max_supply=coin.max_supply,
            ath=coin.ath,
            ath_date=ath_date_ms,
            binance_symbol=coin.binance_symbol,
            updated_at=updated_at_ms,
        )
