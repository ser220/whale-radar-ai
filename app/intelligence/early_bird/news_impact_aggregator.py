"""News impact aggregation for perpetual candidates."""

from dataclasses import dataclass

from app.intelligence.early_bird.candidate_directional_score import (
    CandidateDirectionalScore,
)

from app.intelligence.early_bird.candidate_news_risk import (
    CandidateNewsRisk,
)


@dataclass(frozen=True)
class CandidateAdjustedDirectionScore:
    """
    Direction score after external news adjustment.
    """

    asset: str
    adjusted_long_score: float
    adjusted_short_score: float
    uncertainty_level: float
    confidence: float


class NewsImpactAggregator:
    """
    Applies news risk as a probability modifier.

    News changes confidence and risk,
    not the raw market structure.
    """

    def apply(
        self,
        directional: CandidateDirectionalScore,
        news: CandidateNewsRisk,
    ) -> CandidateAdjustedDirectionScore:

        if directional.asset != news.asset:
            raise ValueError(
                "directional and news asset mismatch"
            )

        long_score = directional.long_score
        short_score = directional.short_score

        pressure = news.news_pressure_score
        uncertainty = news.uncertainty_score

        bias = news.directional_bias.lower()

        if bias == "bearish":

            long_score -= pressure * 0.25
            short_score += pressure * 0.10

        elif bias == "bullish":

            long_score += pressure * 0.20
            short_score -= pressure * 0.10

        else:
            uncertainty = min(
                100.0,
                uncertainty + pressure * 0.20,
            )

        long_score = self._bound(
            long_score
        )

        short_score = self._bound(
            short_score
        )

        confidence = self._bound(
            max(
                long_score,
                short_score,
            ) - uncertainty * 0.20
        )

        return CandidateAdjustedDirectionScore(
            asset=directional.asset,
            adjusted_long_score=round(
                long_score,
                2,
            ),
            adjusted_short_score=round(
                short_score,
                2,
            ),
            uncertainty_level=round(
                uncertainty,
                2,
            ),
            confidence=round(
                confidence,
                2,
            ),
        )

    @staticmethod
    def _bound(
        value: float,
    ) -> float:

        return max(
            0.0,
            min(
                100.0,
                value,
            ),
        )


__all__ = [
    "CandidateAdjustedDirectionScore",
    "NewsImpactAggregator",
]
