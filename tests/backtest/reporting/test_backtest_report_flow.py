from datetime import datetime, timezone

from app.backtest import (
    BacktestPerformanceAggregator,
    BacktestReport,
    BacktestReportGenerator,
    BacktestSessionConfig,
    BacktestSessionResult,
)

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)


def build_trade(
    trade_id: str,
    pnl: float,
) -> PaperTradeResult:

    now = datetime.now(
        timezone.utc
    )

    return PaperTradeResult(
        trade_id=trade_id,
        symbol="BTCUSDT",
        entry_price=65000.0,
        exit_price=65100.0,
        quantity=0.01,
        pnl=pnl,
        closed_at=now,
        status="CLOSED",
    )


def test_backtest_performance_to_report_flow():

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
        processed_snapshots=100,
        generated_trades=4,
        started_at=now,
        finished_at=now,
    )

    trades = [
        build_trade(
            "trade-001",
            100.0,
        ),
        build_trade(
            "trade-002",
            -40.0,
        ),
        build_trade(
            "trade-003",
            50.0,
        ),
        build_trade(
            "trade-004",
            -10.0,
        ),
    ]

    performance = (
        BacktestPerformanceAggregator()
        .aggregate(
            trades
        )
    )

    report = (
        BacktestReportGenerator()
        .generate(
            session=session_result,
            performance=performance,
        )
    )

    assert isinstance(
        report,
        BacktestReport,
    )

    assert (
        report.session.generated_trades
        == 4
    )

    assert (
        report.performance.total_trades
        == 4
    )

    assert (
        report.performance.total_pnl
        == 100.0
    )

    assert (
        report.performance.win_rate
        == 0.5
    )

    assert (
        report.performance.profit_factor
        == 3.0
    )
