from datetime import datetime, timezone

from app.data.market import (
    HistoricalMarketPoint,
    InMemoryMarketDataProvider,
)


def test_in_memory_market_data_provider_loads_points():

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

    result = provider.load()

    assert len(result) == 1

    assert (
        result[0]
        == point
    )

    assert (
        result[0].symbol
        == "BTCUSDT"
    )
