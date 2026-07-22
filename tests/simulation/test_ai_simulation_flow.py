from datetime import datetime, timezone

from app.simulation import (
    SimulationSnapshot,
    SimulationRunner,
)


def test_simulation_accepts_market_history():

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
        SimulationSnapshot(
            symbol="BTCUSDT",
            price=67000.0,
            volume_24h=1000000000.0,
            volatility=0.03,
            timestamp=datetime.now(
                timezone.utc
            ),
        ),
    ]

    runner = SimulationRunner()

    result = runner.run(
        snapshots
    )

    assert (
        result.processed_snapshots
        == 3
    )
