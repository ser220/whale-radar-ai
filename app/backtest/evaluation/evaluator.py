from __future__ import annotations

from app.backtest.performance import (
    BacktestPerformanceReport,
)

from app.backtest.analytics import (
    BacktestAnalyticsReport,
)

from app.backtest.equity import (
    BacktestEquityCurve,
)

from app.backtest.risk import (
    BacktestRiskReport,
)

from app.backtest.benchmark import (
    BacktestBenchmarkReport,
)

from .models import (
    BacktestEvaluationReport,
)


class BacktestEvaluationEvaluator:
    """
    Builds unified strategy evaluation.
    """

    def evaluate(
        self,
        performance: BacktestPerformanceReport,
        analytics: BacktestAnalyticsReport,
        equity: BacktestEquityCurve,
        risk: BacktestRiskReport,
        benchmark: BacktestBenchmarkReport,
    ) -> BacktestEvaluationReport:

        score = self._calculate_score(
            risk,
            benchmark,
        )

        return BacktestEvaluationReport(
            performance=performance,
            analytics=analytics,
            equity=equity,
            risk=risk,
            benchmark=benchmark,
            overall_score=score,
            quality_rating=self._rating(score),
            recommendation=self._recommendation(score),
        )

    def _calculate_score(
        self,
        risk: BacktestRiskReport,
        benchmark: BacktestBenchmarkReport,
    ) -> float:

        score = 50

        score += (
            benchmark.alpha * 100
        )

        score -= (
            risk.max_drawdown_percent * 100
        )

        return max(
            0,
            min(
                100,
                score,
            )
        )

    def _rating(
        self,
        score: float,
    ) -> str:

        if score >= 80:
            return "A"

        if score >= 60:
            return "B"

        if score >= 40:
            return "C"

        return "D"

    def _recommendation(
        self,
        score: float,
    ) -> str:

        if score >= 60:
            return "PASS"

        return "REVIEW"
