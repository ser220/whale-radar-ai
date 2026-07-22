from __future__ import annotations

from app.simulation import (
    SimulationSnapshot,
)

from .models import (
    HistoricalMarketPoint,
)


class HistoricalMarketSimulationAdapter:
    """
    Converts historical market points
    into simulation snapshots.

    Translation only.
    """

    @staticmethod
    def to_snapshot(
        point: HistoricalMarketPoint,
    ) -> SimulationSnapshot:

        if not isinstance(
            point,
            HistoricalMarketPoint,
        ):
            raise TypeError(
                "point must be HistoricalMarketPoint"
            )

        return SimulationSnapshot(
            symbol=point.symbol,
            price=point.price,
            volume_24h=point.volume_24h,
            volatility=point.volatility,
            timestamp=point.captured_at,
        )
