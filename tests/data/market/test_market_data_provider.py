from datetime import datetime, timezone

from app.data.market import (
    HistoricalMarketPoint,
    MarketDataProvider,
)


class DummyMarketDataProvider(
    MarketDataProvider
):
    def load(
        self,
    ) -> list[HistoricalMarketPoint]:

        return [
            HistoricalMarketPoint(
                symbol="BTCUSDT",
                price=65000.0,
                volume_24h=1000000000.0,
                volatility=0.03,
                captured_at=datetime.now(
                    timezone.utc
                ),
            )
        ]


def test_market_data_provider_contract():

    provider = DummyMarketDataProvider()

    points = provider.load()

    assert len(points) == 1

    assert isinstance(
        points[0],
        HistoricalMarketPoint,
    )

    assert (
        points[0].symbol
        == "BTCUSDT"
    )
