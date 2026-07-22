from __future__ import annotations

from app.backtest.performance import (
    BacktestPerformanceReport,
)

from .models import (
    BacktestAnalyticsReport,
)


class BacktestAnalyticsCalculator:
    """
    Calculates analytics from performance report.

    No execution logic.
    No trade lifecycle logic.
    """

    def calculate(
        self,
        performance: BacktestPerformanceReport,
    ) -> BacktestAnalyticsReport:

        if not isinstance(
            performance,
            BacktestPerformanceReport,
        ):
            raise TypeError(
                "performance must be BacktestPerformanceReport"
            )

        return BacktestAnalyticsReport(
            total_return=performance.total_pnl,
            average_trade=performance.average_pnl,
            win_rate=performance.win_rate,
            profit_factor=performance.profit_factor,
            total_trades=performance.total_trades,
        )
