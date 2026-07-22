from __future__ import annotations

from abc import ABC, abstractmethod

from .models import (
    HistoricalMarketPoint,
)


class MarketDataProvider(ABC):
    """
    Boundary for historical market data sources.
    """

    @abstractmethod
    def load(
        self,
    ) -> list[HistoricalMarketPoint]:
        """
        Load historical market points.
        """
        raise NotImplementedError
