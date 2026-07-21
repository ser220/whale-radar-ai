from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MarketFeatures:
    """
    Immutable derived market intelligence features.

    Contains market characteristics only.
    No trading decisions allowed.
    """

    symbol: str
    trend: str
    volatility_state: str
    liquidity_state: str

    def __post_init__(self) -> None:
        symbol = self.symbol.strip()
        trend = self.trend.strip()
        volatility_state = (
            self.volatility_state.strip()
        )
        liquidity_state = (
            self.liquidity_state.strip()
        )

        if not symbol:
            raise ValueError(
                "symbol is required"
            )

        if not trend:
            raise ValueError(
                "trend is required"
            )

        if not volatility_state:
            raise ValueError(
                "volatility_state is required"
            )

        if not liquidity_state:
            raise ValueError(
                "liquidity_state is required"
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "trend",
            trend,
        )

        object.__setattr__(
            self,
            "volatility_state",
            volatility_state,
        )

        object.__setattr__(
            self,
            "liquidity_state",
            liquidity_state,
        )
