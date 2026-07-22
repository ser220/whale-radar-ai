from __future__ import annotations

from typing import Iterable

from app.backtest.recommendation import (
    BacktestRecommendation,
)

from .models import (
    BacktestDecisionReport,
)


class DecisionReportCalculator:
    """
    Builds final decision reports from backtest recommendations.
    """

    def calculate(
        self,
        recommendations: Iterable[BacktestRecommendation],
    ) -> list[BacktestDecisionReport]:
        reports = []

        for recommendation in recommendations:
            if not isinstance(
                recommendation,
                BacktestRecommendation,
            ):
                raise TypeError(
                    "all items must be BacktestRecommendation"
                )

            reports.append(
                BacktestDecisionReport(
                    strategy_id=recommendation.strategy_id,
                    decision=recommendation.decision,
                    rank=recommendation.rank,
                    final_score=recommendation.final_score,
                    confidence=recommendation.confidence,
                    summary=recommendation.reason,
                )
            )

        return reports
