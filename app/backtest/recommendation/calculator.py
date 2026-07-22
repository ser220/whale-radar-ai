from __future__ import annotations

from typing import Iterable

from .models import (
    BacktestRecommendation,
)


class RecommendationCalculator:
    """
    Converts ranked strategies into final recommendations.
    """

    def calculate(
        self,
        strategies: Iterable[dict],
    ) -> list[BacktestRecommendation]:

        recommendations = []

        for strategy in strategies:

            final_score = strategy["final_score"]

            if (
                strategy["rank"] == 1
                and final_score >= 80
            ):
                decision = "PASS"
                confidence = min(
                    final_score / 100,
                    1.0,
                )
                reason = (
                    "Top ranked strategy "
                    "with strong performance"
                )

            elif final_score >= 60:
                decision = "REVIEW"
                confidence = final_score / 100
                reason = (
                    "Strategy requires "
                    "additional review"
                )

            else:
                decision = "REJECT"
                confidence = final_score / 100
                reason = (
                    "Strategy quality "
                    "is below threshold"
                )

            recommendations.append(
                BacktestRecommendation(
                    strategy_id=strategy["strategy_id"],
                    decision=decision,
                    confidence=confidence,
                    reason=reason,
                    final_score=final_score,
                    rank=strategy["rank"],
                )
            )

        return recommendations
