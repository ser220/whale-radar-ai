from app.backtest.equity import (
    BacktestEquityCurve,
)

from app.backtest.risk import (
    BacktestRiskReport,
    RiskMetricsCalculator,
)


def test_risk_metrics_calculation():

    curve = BacktestEquityCurve(
        points=(),
        initial_balance=10000.0,
        final_equity=10800.0,
        cumulative_return=0.08,
        peak_equity=11000.0,
        max_drawdown=200.0,
    )

    report = (
        RiskMetricsCalculator()
        .calculate(
            curve
        )
    )

    assert isinstance(
        report,
        BacktestRiskReport,
    )

    assert (
        report.max_drawdown
        == 200.0
    )

    assert (
        report.max_drawdown_percent
        ==
        200.0 / 11000.0
    )

    assert (
        report.recovery_factor
        == 4.0
    )

    assert (
        report.risk_score
        ==
        1.0 - (200.0 / 11000.0)
    )


def test_zero_drawdown():

    curve = BacktestEquityCurve(
        points=(),
        initial_balance=10000.0,
        final_equity=10500.0,
        cumulative_return=0.05,
        peak_equity=10500.0,
        max_drawdown=0.0,
    )

    report = (
        RiskMetricsCalculator()
        .calculate(
            curve
        )
    )

    assert (
        report.max_drawdown
        == 0.0
    )

    assert (
        report.recovery_factor
        == 0.0
    )


def test_invalid_curve_type():

    try:
        RiskMetricsCalculator().calculate(
            "wrong"
        )

    except TypeError as error:
        assert str(error) == (
            "curve must be BacktestEquityCurve"
        )

    else:
        raise AssertionError(
            "TypeError was not raised"
        )
