from datetime import datetime, timezone

from app.backtest import (
    BacktestSessionConfig,
)


def test_backtest_session_config_creation():

    start = datetime.now(
        timezone.utc
    )

    end = datetime.now(
        timezone.utc
    )

    config = BacktestSessionConfig(
        symbol="BTCUSDT",
        start_time=start,
        end_time=end,
        initial_balance=10000.0,
    )

    assert (
        config.symbol
        == "BTCUSDT"
    )

    assert (
        config.initial_balance
        == 10000.0
    )


def test_backtest_session_config_rejects_invalid_balance():

    start = datetime.now(
        timezone.utc
    )

    end = datetime.now(
        timezone.utc
    )

    try:
        BacktestSessionConfig(
            symbol="BTCUSDT",
            start_time=start,
            end_time=end,
            initial_balance=0,
        )

        assert False

    except ValueError:
        assert True
