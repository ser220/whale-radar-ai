"""Market universe provider contract."""

from app.data.market.market_universe import MarketUniverse


class MarketUniverseProvider:
    """
    Boundary contract for market universe sources.

    Concrete providers may use exchanges,
    aggregators, or other sources.
    """

    def build(self) -> MarketUniverse:
        raise NotImplementedError(
            "MarketUniverseProvider.build() must be implemented"
        )


__all__ = [
    "MarketUniverseProvider",
]
