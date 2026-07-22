from __future__ import annotations

from app.intelligence.market import (
    MarketSnapshot,
)

from .models import (
    SimulationSnapshot,
)


class SimulationMarketAdapter:
    """
    Converts simulation market points
    into intelligence market snapshots.

    Translation only.
    No strategy logic.
    """

    @staticmethod
    def to_market_snapshot(
        snapshot: SimulationSnapshot,
    ) -> MarketSnapshot:

        if not isinstance(
            snapshot,
            SimulationSnapshot,
        ):
            raise TypeError(
                "snapshot must be SimulationSnapshot"
            )

        return MarketSnapshot(
            symbol=snapshot.symbol,
            price=snapshot.price,
            volume_24h=snapshot.volume_24h,
            volatility=snapshot.volatility,
            captured_at=snapshot.timestamp,
        )
