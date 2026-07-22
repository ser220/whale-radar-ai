from datetime import datetime, timezone

from app.data.market import (
    HistoricalMarketPoint,
    InMemoryMarketDataProvider,
    HistoricalSimulationFeed,
)

from app.simulation import (
    SimulationRunner,
    SimulationSnapshot,
)


class DummyStrategy:

    def should_open_trade(
        self,
        snapshot: SimulationSnapshot,
    ) -> bool:

        return True


def test_market_data_to_simulation_runner_flow():

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

    feed = HistoricalSimulationFeed(
        provider.load()
    )

    runner = SimulationRunner(
        strategy=DummyStrategy()
    )

    result = runner.run(
        feed.snapshots()
    )

    assert (
        result.processed_snapshots
        == 1
    )
