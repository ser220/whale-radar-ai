from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class MarketSnapshot:
    """
    Immutable normalized market intelligence snapshot.
    """

    symbol: str
    price: float
    volume_24h: float
    volatility: float
    captured_at: datetime

    def __post_init__(self) -> None:
        symbol = self.symbol.strip()

        if not symbol:
            raise ValueError(
                "symbol is required"
            )

        if self.price <= 0:
            raise ValueError(
                "price must be positive"
            )

        if self.volume_24h < 0:
            raise ValueError(
                "volume_24h cannot be negative"
            )

        if self.volatility < 0:
            raise ValueError(
                "volatility cannot be negative"
            )

        if self.captured_at.tzinfo is None:
            raise ValueError(
                "captured_at must be timezone-aware"
            )

        object.__setattr__(
            self,
            "symbol",
            symbol,
        )

        object.__setattr__(
            self,
            "captured_at",
            self.captured_at.astimezone(
                timezone.utc
            ),
        )
