from __future__ import annotations

from .strategy_adapter import (
    SimulationStrategyAdapter,
)


class AISimulationStrategyAdapter(
    SimulationStrategyAdapter
):
    """
    Connects simulation with AI decision layer.

    Decision logic will be injected later.
    """

    def should_open_trade(
        self,
        snapshot,
    ) -> bool:

        return False
