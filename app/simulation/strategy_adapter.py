from __future__ import annotations


class SimulationStrategyAdapter:
    """
    Boundary between simulation engine
    and decision logic.
    """

    def should_open_trade(
        self,
        snapshot,
    ) -> bool:
        return False
