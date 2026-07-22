from datetime import datetime, timezone

from app.simulation import (
    SimulationRunner,
    SimulationSnapshot,
    SimulationStrategyAdapter,
)


class AlwaysBuyStrategy(
    SimulationStrategyAdapter
):
    def should_open_trade(
        self,
        snapshot,
    ) -> bool:
        return True


def test_simulation_generates_paper_trades():

    snapshots = [
        SimulationSnapshot(
            symbol="BTCUSDT",
            price=65000.0,
            volume_24h=1000000000.0,
            volatility=0.03,
            timestamp=datetime.now(
                timezone.utc
            ),
        ),
        SimulationSnapshot(
            symbol="BTCUSDT",
            price=66000.0,
            volume_24h=1000000000.0,
            volatility=0.03,
            timestamp=datetime.now(
                timezone.utc
            ),
        ),
    ]

    runner = SimulationRunner(
        strategy=AlwaysBuyStrategy()
    )

    result = runner.run(
        snapshots
    )

    assert (
        result.processed_snapshots
        == 2
    )

    assert (
        result.generated_trades
        == 2
    )
