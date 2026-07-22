from __future__ import annotations

from app.data.market.models import (
    HistoricalMarketPoint,
)

from app.data.market.provider import (
    MarketDataProvider,
)


class InMemoryMarketDataProvider(
    MarketDataProvider
):
    """
    In-memory historical market data provider.

    Used for simulation and testing.
    """

    def __init__(
        self,
        points: list[HistoricalMarketPoint],
    ) -> None:
        self._points = list(points)

    def load(
        self,
    ) -> list[HistoricalMarketPoint]:

        return list(
            self._points
        )
