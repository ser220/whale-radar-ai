"""Directional analyzer for perpetual candidates."""

from app.intelligence.early_bird.candidate_directional_score import (
    CandidateDirectionalScore,
)


class DirectionalAnalyzer:
    """
    Evaluates both LONG and SHORT opportunity.
    """

    def analyze(
        self,
        signals: dict,
    ) -> CandidateDirectionalScore:

        momentum = float(
            signals.get("momentum", 0)
        )

        volume = float(
            signals.get("volume", 0)
        )

        oi_health = float(
            signals.get("oi_health", 0)
        )

        exhaustion = float(
            signals.get("exhaustion", 0)
        )

        bearish_structure = float(
            signals.get("bearish_structure", 0)
        )

        long_score = (
            momentum * 0.4
            + volume * 0.3
            + oi_health * 0.2
            - exhaustion * 0.1
            - bearish_structure * 0.1
        )

        short_score = (
            exhaustion * 0.4
            + bearish_structure * 0.35
            + oi_health * 0.2
            - momentum * 0.15
        )

        long_score = self._bound(
            long_score
        )

        short_score = self._bound(
            short_score
        )

        regime = self._regime(
            long_score,
            short_score,
            exhaustion,
            bearish_structure,
        )

        return CandidateDirectionalScore(
            asset="UNKNOWN",
            long_score=round(
                long_score,
                2,
            ),
            short_score=round(
                short_score,
                2,
            ),
            long_rank=self._rank(
                long_score,
                "L",
            ),
            short_rank=self._rank(
                short_score,
                "S",
            ),
            market_regime=regime,
            confidence=round(
                max(
                    long_score,
                    short_score,
                ),
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

    @staticmethod
    def _rank(
        score: float,
        prefix: str,
    ) -> str:

        if score >= 80:
            return f"{prefix}4"

        if score >= 60:
            return f"{prefix}3"

        if score >= 40:
            return f"{prefix}2"

        return f"{prefix}1"

    @staticmethod
    def _regime(
        long_score,
        short_score,
        exhaustion,
        bearish_structure,
    ):

        if (
            exhaustion >= 70
            and bearish_structure >= 70
        ):
            return "bullish_exhaustion"

        if long_score >= 70:
            return "bullish_continuation"

        if short_score >= 70:
            return "bearish_continuation"

        return "neutral"


__all__ = [
    "DirectionalAnalyzer",
]
