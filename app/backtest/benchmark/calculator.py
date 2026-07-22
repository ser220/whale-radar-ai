from __future__ import annotations

from app.backtest.benchmark.models import (
    BacktestBenchmarkReport,
)


class BenchmarkCalculator:
    """
    Calculates strategy performance
    against passive benchmark.
    """

    def calculate(
        self,
        strategy_return: float,
        benchmark_return: float,
    ) -> BacktestBenchmarkReport:
        """
        Compare strategy result
        with benchmark result.
        """

        alpha = (
            strategy_return
            -
            benchmark_return
        )

        outperformance = alpha

        benchmark_win = (
            strategy_return
            >
            benchmark_return
        )

        return BacktestBenchmarkReport(
            strategy_return=strategy_return,
            benchmark_return=benchmark_return,
            alpha=alpha,
            outperformance=outperformance,
            benchmark_win=benchmark_win,
        )
