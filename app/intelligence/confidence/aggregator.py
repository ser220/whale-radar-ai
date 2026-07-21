from __future__ import annotations

from app.intelligence.scoring import (
    IntelligenceScore,
)

from app.intelligence.risk import (
    RiskAssessment,
)

from .models import DecisionConfidence


class ConfidenceAggregator:
    """
    Combines intelligence quality and risk.

    Aggregation only.
    No trading decisions.
    """

    @staticmethod
    def aggregate(
        score: IntelligenceScore,
        risk: RiskAssessment,
    ) -> DecisionConfidence:

        if not isinstance(
            score,
            IntelligenceScore,
        ):
            raise TypeError(
                "score must be IntelligenceScore"
            )

        if not isinstance(
            risk,
            RiskAssessment,
        ):
            raise TypeError(
                "risk must be RiskAssessment"
            )

        risk_penalty = (
            risk.risk_score / 100
        )

        confidence = (
            score.confidence
            *
            (1 - risk_penalty)
        )

        if confidence >= 0.75:
            level = "high"
        elif confidence >= 0.45:
            level = "medium"
        else:
            level = "low"

        return DecisionConfidence(
            symbol=score.symbol,
            confidence=round(
                confidence,
                4,
            ),
            level=level,
        )
