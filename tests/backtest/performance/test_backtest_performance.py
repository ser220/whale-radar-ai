from datetime import datetime, timezone

from app.backtest import (
    BacktestPerformanceAggregator,
    BacktestPerformanceReport,
)

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)


def build_trade(
    trade_id: str,
    pnl: float,
) -> PaperTradeResult:

    return PaperTradeResult(
        trade_id=trade_id,
        symbol="BTCUSDT",
        entry_price=65000.0,
        exit_price=65100.0,
        quantity=0.01,
        pnl=pnl,
        closed_at=datetime.now(
            timezone.utc
        ),
        status="CLOSED",
    )


def test_performance_report_model():

    report = BacktestPerformanceReport(
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        total_pnl=120.0,
        average_pnl=12.0,
        win_rate=0.6,
        profit_factor=2.0,
    )

    assert (
        report.total_trades
        == 10
    )

    assert (
        report.win_rate
        == 0.6
    )


def test_performance_aggregator():

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

    aggregator = BacktestPerformanceAggregator()

    report = aggregator.aggregate(
        trades
    )

    assert (
        report.total_trades
        == 4
    )

    assert (
        report.winning_trades
        == 2
    )

    assert (
        report.losing_trades
        == 2
    )

    assert (
        report.total_pnl
        == 100.0
    )

    assert (
        report.win_rate
        == 0.5
    )

    assert (
        report.profit_factor
        == 3.0
    )
