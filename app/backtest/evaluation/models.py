from __future__ import annotations

from dataclasses import dataclass

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


@dataclass(frozen=True)
class BacktestEvaluationReport:
    """
    Unified backtest strategy evaluation result.
    """

    performance: BacktestPerformanceReport
    analytics: BacktestAnalyticsReport
    equity: BacktestEquityCurve
    risk: BacktestRiskReport
    benchmark: BacktestBenchmarkReport

    overall_score: float
    quality_rating: str
    recommendation: str

    def __post_init__(self) -> None:

        if self.overall_score < 0:
            raise ValueError(
                "overall_score cannot be negative"
            )

        if self.overall_score > 100:
            raise ValueError(
                "overall_score cannot exceed 100"
            )
