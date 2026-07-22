from datetime import datetime, timezone

from app.data.market import (
    HistoricalMarketPoint,
    HistoricalMarketSimulationAdapter,
)

from app.simulation import (
    SimulationSnapshot,
)


def test_historical_market_point_to_simulation_snapshot():

    point = HistoricalMarketPoint(
        symbol="BTCUSDT",
        price=65000.0,
        volume_24h=1000000000.0,
        volatility=0.03,
        captured_at=datetime.now(
            timezone.utc
        ),
    )

    snapshot = (
        HistoricalMarketSimulationAdapter
        .to_snapshot(
            point
        )
    )

    assert isinstance(
        snapshot,
        SimulationSnapshot,
    )

    assert (
        snapshot.symbol
        == "BTCUSDT"
    )

    assert (
        snapshot.price
        == 65000.0
    )
