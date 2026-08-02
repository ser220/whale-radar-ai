"""Static market universe provider."""

from typing import Iterable

from app.data.market.market_universe import (
    MarketUniverse,
)


class StaticMarketUniverseProvider:
    """Build a fixed market universe."""

    def __init__(
        self,
        assets: Iterable[str] = (),
    ) -> None:
        self._assets = tuple(assets)

    def build(self) -> MarketUniverse:
        return MarketUniverse(
            assets=self._assets,
        )


__all__ = [
    "StaticMarketUniverseProvider",
]
