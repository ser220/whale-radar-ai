from app.backtest.review.models import (
    BacktestAIReview,
)


class AIReviewGenerator:
    """
    Produces a final AI-style review from
    a backtest AI summary.
    """

    def generate(
        self,
        strategy_id: str,
        decision: str,
        confidence: float,
    ) -> BacktestAIReview:

        if decision == "PASS":

            verdict = "APPROVE"
            readiness = "READY"

            strengths = (
                "Strong backtest performance",
                "Acceptable risk profile",
            )

            risks = (
                "Future market conditions may differ",
            )

            actions = (
                "Deploy with standard monitoring",
            )

        elif decision == "REVIEW":

            verdict = "CONDITIONAL"
            readiness = "LIMITED"

            strengths = (
                "Shows potential",
            )

            risks = (
                "Requires additional validation",
            )

            actions = (
                "Perform extended testing",
            )

        else:

            verdict = "REJECT"
            readiness = "NOT_READY"

            strengths = (
                "Backtest completed",
            )

            risks = (
                "Performance below acceptance criteria",
            )

            actions = (
                "Revise strategy before retesting",
            )

        return BacktestAIReview(
            strategy_id=strategy_id,
            verdict=verdict,
            production_readiness=readiness,
            strengths=strengths,
            risks=risks,
            recommended_actions=actions,
            confidence=confidence,
        )
