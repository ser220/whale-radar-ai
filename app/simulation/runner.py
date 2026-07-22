from __future__ import annotations

from typing import Iterable

from .models import (
    SimulationResult,
    SimulationSnapshot,
)

from .strategy_adapter import (
    SimulationStrategyAdapter,
)


class SimulationRunner:
    """
    Executes historical market simulation.

    Strategy is injected through adapter.
    """

    def __init__(
        self,
        strategy: SimulationStrategyAdapter | None = None,
    ) -> None:

        self._strategy = (
            strategy
            or SimulationStrategyAdapter()
        )

    def run(
        self,
        snapshots: Iterable[SimulationSnapshot],
    ) -> SimulationResult:

        snapshots = list(
            snapshots
        )

        for snapshot in snapshots:
            if not isinstance(
                snapshot,
                SimulationSnapshot,
            ):
                raise TypeError(
                    "all items must be SimulationSnapshot"
                )

        generated_trades = 0

        for snapshot in snapshots:
            if self._strategy.should_open_trade(
                snapshot
            ):
                generated_trades += 1

        return SimulationResult(
            processed_snapshots=len(
                snapshots
            ),
            generated_trades=generated_trades,
        )
