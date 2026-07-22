from app.backtest.analytics import (
    BacktestAnalyticsCalculator,
    BacktestAnalyticsReport,
)

from app.backtest.performance import (
    BacktestPerformanceAggregator,
)

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)

from datetime import datetime, timezone


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


def test_performance_to_analytics_flow():

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

    analytics = (
        BacktestAnalyticsCalculator()
        .calculate(
            performance
        )
    )

    assert isinstance(
        analytics,
        BacktestAnalyticsReport,
    )

    assert (
        analytics.total_return
        == 100.0
    )

    assert (
        analytics.total_trades
        == 4
    )

    assert (
        analytics.win_rate
        == 0.5
    )

    assert (
        analytics.profit_factor
        == 3.0
    )
