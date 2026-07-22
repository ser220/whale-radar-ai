from datetime import datetime, timezone

from app.data.market import (
    HistoricalMarketPoint,
    InMemoryMarketDataProvider,
    HistoricalSimulationFeed,
)

from app.simulation import (
    SimulationSnapshot,
)


def test_market_data_provider_to_simulation_flow():

    point = HistoricalMarketPoint(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.03,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    provider = InMemoryMarketDataProvider(
        [
            point,
        ]
    )

    historical_points = provider.load()

    feed = HistoricalSimulationFeed(
        historical_points
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

    assert (
        snapshots[0].price
        == 65000.0
    )
