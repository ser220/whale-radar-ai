from datetime import datetime, timezone

from app.data.market import (
    HistoricalMarketPoint,
    HistoricalSimulationFeed,
)

from app.simulation import (
    SimulationSnapshot,
)


def test_historical_simulation_feed_creates_snapshots():

    point = HistoricalMarketPoint(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.03,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    feed = HistoricalSimulationFeed(
        [
            point,
        ]
    )

    snapshots = feed.snapshots()

    assert len(snapshots) == 1

    assert isinstance(
        snapshots[0],
        SimulationSnapshot,
    )

    assert (
        snapshots[0].symbol
        == "BTCUSDT"
    )
