from datetime import datetime, timezone

from app.data.market import (
    HistoricalMarketPoint,
    InMemoryMarketDataProvider,
    HistoricalSimulationFeed,
)

from app.backtest import (
    BacktestSessionConfig,
    BacktestSessionService,
)


def build_config() -> BacktestSessionConfig:

    now = datetime.now(
        timezone.utc
    )

    return BacktestSessionConfig(
        symbol="BTCUSDT",
        start_time=now,
        end_time=now,
        initial_balance=10000.0,
    )


def test_historical_data_to_backtest_session_flow():

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

    service = BacktestSessionService()

    result = service.run(
        build_config(),
        feed.snapshots(),
    )

    assert (
        result.processed_snapshots
        == 1
    )

    assert (
        result.config.symbol
        == "BTCUSDT"
    )

    assert (
        result.config.initial_balance
        == 10000.0
    )

    assert (
        result.finished_at
        >= result.started_at
    )
