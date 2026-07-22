from datetime import datetime, timezone, timedelta

from app.backtest.equity import (
    EquityCurveCalculator,
)

from app.backtest.risk import (
    BacktestRiskReport,
    RiskMetricsCalculator,
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


def test_equity_to_risk_flow():

    start = datetime.now(
        timezone.utc
    )

    trades = [
        build_trade(
            "trade-001",
            500.0,
            start,
        ),
        build_trade(
            "trade-002",
            -200.0,
            start + timedelta(minutes=15),
        ),
        build_trade(
            "trade-003",
            300.0,
            start + timedelta(minutes=30),
        ),
        build_trade(
            "trade-004",
            -400.0,
            start + timedelta(minutes=45),
        ),
    ]

    curve = (
        EquityCurveCalculator()
        .calculate(
            trades=trades,
            initial_balance=10000.0,
        )
    )

    risk = (
        RiskMetricsCalculator()
        .calculate(
            curve
        )
    )

    assert isinstance(
        risk,
        BacktestRiskReport,
    )

    assert (
        risk.max_drawdown
        == 400.0
    )

    assert (
        risk.max_drawdown_percent
        ==
        400.0 / 10600.0
    )

    assert (
        risk.recovery_factor
        == 0.5
    )
