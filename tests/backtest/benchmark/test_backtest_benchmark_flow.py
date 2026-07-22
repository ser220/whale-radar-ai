from app.backtest.benchmark import (
    BacktestBenchmarkReport,
    BenchmarkCalculator,
)

from app.backtest.performance import (
    BacktestPerformanceReport,
)


def test_performance_to_benchmark_flow():

    performance = BacktestPerformanceReport(
        total_trades=10,
        winning_trades=7,
        losing_trades=3,
        total_pnl=500.0,
        average_pnl=50.0,
        win_rate=0.7,
        profit_factor=2.5,
    )

    initial_balance = 10000.0

    strategy_return = (
        performance.total_pnl
        /
        initial_balance
    )

    report = (
        BenchmarkCalculator()
        .calculate(
            strategy_return=strategy_return,
            benchmark_return=0.03,
        )
    )

    assert isinstance(
        report,
        BacktestBenchmarkReport,
    )

    assert (
        report.strategy_return
        == 0.05
    )

    assert (
        report.benchmark_return
        == 0.03
    )

    assert round(
        report.alpha,
        10,
    ) == 0.02

    assert round(
        report.outperformance,
        10,
    ) == 0.02

    assert (
        report.benchmark_win
        is True
    )
