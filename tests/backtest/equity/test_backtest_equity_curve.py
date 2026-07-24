from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone

import pytest

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


def test_equity_curve_defensively_preserves_list_points() -> None:
    first = EquityPoint(
        timestamp=datetime(
            2026,
            7,
            22,
            9,
            0,
            tzinfo=timezone.utc,
        ),
        equity=10000.0,
    )
    second = EquityPoint(
        timestamp=datetime(
            2026,
            7,
            22,
            9,
            15,
            tzinfo=timezone.utc,
        ),
        equity=10100.0,
    )
    points = [
        first,
        second,
        first,
    ]

    curve = BacktestEquityCurve(
        points=points,
        initial_balance=10000.0,
        final_equity=10100.0,
        cumulative_return=0.01,
        peak_equity=10100.0,
        max_drawdown=0.0,
    )

    assert isinstance(
        curve.points,
        tuple,
    )
    assert curve.points == (
        first,
        second,
        first,
    )
    assert curve.points[0] is first
    assert curve.points[1] is second
    assert curve.points[2] is first

    points.reverse()
    points.clear()

    assert curve.points == (
        first,
        second,
        first,
    )


def test_equity_curve_tuple_input_remains_valid() -> None:
    point = EquityPoint(
        timestamp=datetime(
            2026,
            7,
            22,
            10,
            0,
            tzinfo=timezone.utc,
        ),
        equity=10000.0,
    )

    curve = BacktestEquityCurve(
        points=(
            point,
        ),
        initial_balance=10000.0,
        final_equity=10000.0,
        cumulative_return=0.0,
        peak_equity=10000.0,
        max_drawdown=0.0,
    )

    assert curve.points == (
        point,
    )
    assert curve.points[0] is point


def test_equity_curve_empty_list_becomes_empty_tuple() -> None:
    curve = BacktestEquityCurve(
        points=[],
        initial_balance=10000.0,
        final_equity=10000.0,
        cumulative_return=0.0,
        peak_equity=10000.0,
        max_drawdown=0.0,
    )

    assert curve.points == ()
    assert isinstance(
        curve.points,
        tuple,
    )


@pytest.mark.parametrize(
    (
        "initial_balance",
        "final_equity",
        "max_drawdown",
        "message",
    ),
    [
        (
            0.0,
            10000.0,
            0.0,
            "initial_balance must be positive",
        ),
        (
            10000.0,
            -1.0,
            0.0,
            "final_equity cannot be negative",
        ),
        (
            10000.0,
            10000.0,
            -1.0,
            "max_drawdown cannot be negative",
        ),
    ],
)
def test_equity_curve_scalar_validation_precedes_points_conversion(
    initial_balance: float,
    final_equity: float,
    max_drawdown: float,
    message: str,
) -> None:
    with pytest.raises(ValueError) as raised:
        BacktestEquityCurve(
            points=object(),
            initial_balance=initial_balance,
            final_equity=final_equity,
            cumulative_return=0.0,
            peak_equity=10000.0,
            max_drawdown=max_drawdown,
        )

    assert str(raised.value) == message


def test_equity_curve_remains_frozen() -> None:
    curve = BacktestEquityCurve(
        points=(),
        initial_balance=10000.0,
        final_equity=10000.0,
        cumulative_return=0.0,
        peak_equity=10000.0,
        max_drawdown=0.0,
    )

    with pytest.raises(FrozenInstanceError):
        curve.points = ()
