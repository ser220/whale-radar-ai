from __future__ import annotations

from app.intelligence.features import (
    MarketFeatures,
)

from app.intelligence.scoring import (
    IntelligenceScore,
)

from .models import RiskAssessment


class RiskEvaluator:
    """
    Evaluates market risk conditions.

    No trading decisions.
    No execution logic.
    """

    @staticmethod
    def evaluate(
        features: MarketFeatures,
        score: IntelligenceScore,
    ) -> RiskAssessment:

        if not isinstance(
            features,
            MarketFeatures,
        ):
            raise TypeError(
                "features must be MarketFeatures"
            )

        if not isinstance(
            score,
            IntelligenceScore,
        ):
            raise TypeError(
                "score must be IntelligenceScore"
            )

        risk = 50
        reasons = []

        if (
            features.volatility_state
            == "high"
        ):
            risk += 30
            reasons.append(
                "high volatility"
            )
        else:
            risk -= 10
            reasons.append(
                "normal volatility"
            )

        if (
            features.liquidity_state
            == "healthy"
        ):
            risk -= 20
            reasons.append(
                "healthy liquidity"
            )
        else:
            risk += 20
            reasons.append(
                "poor liquidity"
            )

        if score.score < 50:
            risk += 20
            reasons.append(
                "weak intelligence score"
            )

        risk = max(
            0,
            min(
                100,
                risk,
            ),
        )

        if risk < 30:
            level = "low"
        elif risk < 70:
            level = "medium"
        else:
            level = "high"

        return RiskAssessment(
            symbol=features.symbol,
            risk_level=level,
            risk_score=float(risk),
            reasons=tuple(reasons),
        )
