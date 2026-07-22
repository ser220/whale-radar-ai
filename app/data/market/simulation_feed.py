from __future__ import annotations

from app.simulation import (
    SimulationSnapshot,
)

from .models import (
    HistoricalMarketPoint,
)

from .simulation_adapter import (
    HistoricalMarketSimulationAdapter,
)


class HistoricalSimulationFeed:
    """
    Converts historical market points
    into simulation snapshots.
    """

    def __init__(
        self,
        points: list[HistoricalMarketPoint],
    ) -> None:
        self._points = list(points)

    def snapshots(
        self,
    ) -> list[SimulationSnapshot]:

        return [
            HistoricalMarketSimulationAdapter
            .to_snapshot(point)
            for point in self._points
        ]
