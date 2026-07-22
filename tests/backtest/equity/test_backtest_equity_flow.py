from datetime import datetime, timezone, timedelta

from app.backtest.equity import (
    BacktestEquityCurve,
    EquityCurveCalculator,
)

from app.backtest.performance import (
    BacktestPerformanceAggregator,
)

from app.execution.paper_lifecycle import (
    PaperTradeResult,
)


def build_trade(
    trade_id: str,
    pnl: float,
    closed_at: datetime,
) -> PaperTradeResult:

    return PaperTradeResult(
        trade_id=trade_id,
        symbol="BTCUSDT",
        entry_price=65000.0,
        exit_price=65100.0,
        quantity=0.01,
        pnl=pnl,
        closed_at=closed_at,
        status="CLOSED",
    )


def test_performance_to_equity_flow():

    start = datetime.now(
        timezone.utc
    )

    trades = [
        build_trade(
            "trade-001",
            100.0,
            start,
        ),
        build_trade(
            "trade-002",
            -50.0,
            start + timedelta(minutes=15),
        ),
        build_trade(
            "trade-003",
            200.0,
            start + timedelta(minutes=30),
        ),
    ]

    performance = (
        BacktestPerformanceAggregator()
        .aggregate(
            trades
        )
    )

    curve = (
        EquityCurveCalculator()
        .calculate(
            trades=trades,
            initial_balance=10000.0,
        )
    )

    assert isinstance(
        curve,
        BacktestEquityCurve,
    )

    assert (
        performance.total_trades
        == len(trades)
    )

    assert (
        curve.final_equity
        == 10250.0
    )

    assert (
        curve.peak_equity
        == 10250.0
    )

    assert (
        curve.max_drawdown
        == 50.0
    )
