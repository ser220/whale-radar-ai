from datetime import datetime, timezone

from app.backtest import (
    BacktestPerformanceAggregator,
    BacktestSessionResult,
    BacktestSessionConfig,
)

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)


def test_backtest_to_performance_flow():

    now = datetime.now(
        timezone.utc
    )

    config = BacktestSessionConfig(
        symbol="BTCUSDT",
        start_time=now,
        end_time=now,
        initial_balance=10000.0,
    )

    session_result = BacktestSessionResult(
        config=config,
        processed_snapshots=10,
        generated_trades=2,
        started_at=now,
        finished_at=now,
    )

    trades = [
        PaperTradeResult(
            trade_id="trade-001",
            symbol="BTCUSDT",
            entry_price=65000.0,
            exit_price=65100.0,
            quantity=0.01,
            pnl=1.0,
            closed_at=now,
            status="CLOSED",
        ),
        PaperTradeResult(
            trade_id="trade-002",
            symbol="BTCUSDT",
            entry_price=65000.0,
            exit_price=64900.0,
            quantity=0.01,
            pnl=-1.0,
            closed_at=now,
            status="CLOSED",
        ),
    ]

    aggregator = BacktestPerformanceAggregator()

    report = aggregator.aggregate(
        trades
    )

    assert (
        session_result.generated_trades
        == report.total_trades
    )

    assert (
        report.win_rate
        == 0.5
    )
