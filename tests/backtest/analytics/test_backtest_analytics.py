from app.backtest.analytics import (
    BacktestAnalyticsCalculator,
    BacktestAnalyticsReport,
)

from app.backtest.performance import (
    BacktestPerformanceReport,
)


def build_performance():

    return BacktestPerformanceReport(
        total_trades=10,
        winning_trades=6,
        losing_trades=4,
        total_pnl=200.0,
        average_pnl=20.0,
        win_rate=0.6,
        profit_factor=2.5,
    )


def test_analytics_report():

    calculator = BacktestAnalyticsCalculator()

    report = calculator.calculate(
        build_performance()
    )

    assert isinstance(
        report,
        BacktestAnalyticsReport,
    )

    assert (
        report.total_return
        == 200.0
    )

    assert (
        report.win_rate
        == 0.6
    )

    assert (
        report.profit_factor
        == 2.5
    )
