from __future__ import annotations

from app.intelligence.features import (
    MarketFeatures,
)

from .models import IntelligenceScore


class IntelligenceScorer:
    """
    Converts MarketFeatures into IntelligenceScore.

    Scoring only.
    No trading decisions.
    """

    @staticmethod
    def score(
        features: MarketFeatures,
    ) -> IntelligenceScore:

        if not isinstance(
            features,
            MarketFeatures,
        ):
            raise TypeError(
                "features must be MarketFeatures"
            )

        value = 0

        if features.trend == "bullish":
            value += 40

        if (
            features.volatility_state
            == "normal"
        ):
            value += 30

        if (
            features.liquidity_state
            == "healthy"
        ):
            value += 30

        return IntelligenceScore(
            symbol=features.symbol,
            score=float(value),
            confidence=(
                float(value) / 100
            ),
        )
