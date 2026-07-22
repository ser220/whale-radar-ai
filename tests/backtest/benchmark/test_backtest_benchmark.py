from app.backtest.benchmark import (
    BacktestBenchmarkReport,
    BenchmarkCalculator,
)


def test_benchmark_calculation():

    calculator = BenchmarkCalculator()

    report = calculator.calculate(
        strategy_return=0.25,
        benchmark_return=0.10,
    )

    assert isinstance(
        report,
        BacktestBenchmarkReport,
    )

    assert (
        report.strategy_return
        == 0.25
    )

    assert (
        report.benchmark_return
        == 0.10
    )

    assert (
        report.alpha
        == 0.15
    )

    assert (
        report.outperformance
        == 0.15
    )

    assert (
        report.benchmark_win
        is True
    )
