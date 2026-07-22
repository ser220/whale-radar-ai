from __future__ import annotations

from app.backtest.session import (
    BacktestSessionResult,
)

from app.backtest.performance import (
    BacktestPerformanceReport,
)

from .models import (
    BacktestReport,
)


class BacktestReportGenerator:
    """
    Combines session and performance results.

    No execution logic.
    No calculation logic.
    """

    def generate(
        self,
        session: BacktestSessionResult,
        performance: BacktestPerformanceReport,
    ) -> BacktestReport:

        return BacktestReport(
            session=session,
            performance=performance,
        )
