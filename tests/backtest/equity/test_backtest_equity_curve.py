from datetime import datetime, timedelta, timezone

from app.backtest.equity import (
    BacktestEquityCurve,
    EquityCurveCalculator,
    EquityPoint,
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


def test_equity_curve_calculator():

    started_at = datetime(
        2026,
        7,
        22,
        8,
        0,
        tzinfo=timezone.utc,
    )

    trades = [
        build_trade(
            trade_id="trade-001",
            pnl=100.0,
            closed_at=started_at,
        ),
        build_trade(
            trade_id="trade-002",
            pnl=-40.0,
            closed_at=started_at
            + timedelta(minutes=15),
        ),
        build_trade(
            trade_id="trade-003",
            pnl=50.0,
            closed_at=started_at
            + timedelta(minutes=30),
        ),
        build_trade(
            trade_id="trade-004",
            pnl=-200.0,
            closed_at=started_at
            + timedelta(minutes=45),
        ),
    ]

    curve = EquityCurveCalculator().calculate(
        trades=trades,
        initial_balance=10000.0,
    )

    assert isinstance(
        curve,
        BacktestEquityCurve,
    )

    assert curve.points == (
        EquityPoint(
            timestamp=started_at,
            equity=10100.0,
        ),
        EquityPoint(
            timestamp=started_at
            + timedelta(minutes=15),
            equity=10060.0,
        ),
        EquityPoint(
            timestamp=started_at
            + timedelta(minutes=30),
            equity=10110.0,
        ),
        EquityPoint(
            timestamp=started_at
            + timedelta(minutes=45),
            equity=9910.0,
        ),
    )

    assert curve.initial_balance == 10000.0
    assert curve.final_equity == 9910.0
    assert curve.cumulative_return == -0.009
    assert curve.peak_equity == 10110.0
    assert curve.max_drawdown == 200.0


def test_empty_trade_collection():

    curve = EquityCurveCalculator().calculate(
        trades=[],
        initial_balance=10000.0,
    )

    assert curve.points == ()
    assert curve.final_equity == 10000.0
    assert curve.cumulative_return == 0.0
    assert curve.peak_equity == 10000.0
    assert curve.max_drawdown == 0.0


def test_initial_balance_must_be_positive():

    try:
        EquityCurveCalculator().calculate(
            trades=[],
            initial_balance=0.0,
        )
    except ValueError as error:
        assert str(error) == (
            "initial_balance must be positive"
        )
    else:
        raise AssertionError(
            "ValueError was not raised"
        )
