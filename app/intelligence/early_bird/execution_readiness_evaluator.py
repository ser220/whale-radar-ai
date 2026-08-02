"""Execution readiness evaluator."""

from app.intelligence.early_bird.perpetual_execution_readiness import (
    PerpetualExecutionReadiness,
)


class ExecutionReadinessEvaluator:
    """
    Evaluates whether perpetual opportunity
    is suitable for execution.
    """

    def evaluate(
        self,
        opportunity,
        *,
        risk_score: float,
        news_risk: float,
    ) -> PerpetualExecutionReadiness:

        status = self._resolve_status(
            opportunity,
            risk_score,
            news_risk,
        )

        return PerpetualExecutionReadiness(
            asset=opportunity.asset,
            direction=opportunity.direction,
            status=status,
            confidence=opportunity.confidence,
            risk_score=risk_score,
            news_risk=news_risk,
            reason=self._reason(
                status,
                opportunity,
            ),
        )

    @staticmethod
    def _resolve_status(
        opportunity,
        risk_score,
        news_risk,
    ) -> str:

        if (
            news_risk > 70.0
            or risk_score > 70.0
            or opportunity.confidence < 60.0
        ):
            return "WAIT"

        if (
            opportunity.confidence >= 80.0
            and risk_score <= 50.0
            and news_risk <= 40.0
        ):
            return "READY"

        return "PREPARE"

    @staticmethod
    def _reason(
        status,
        opportunity,
    ) -> str:

        if status == "READY":
            return (
                "execution conditions confirmed"
            )

        if status == "WAIT":
            return (
                "risk or uncertainty too high"
            )

        return (
            "candidate requires confirmation"
        )


__all__ = [
    "ExecutionReadinessEvaluator",
]
