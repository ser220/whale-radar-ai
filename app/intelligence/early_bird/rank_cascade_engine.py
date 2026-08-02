"""Dual directional rank cascade engine."""

from app.intelligence.early_bird.candidate_dual_rank import (
    CandidateDualRank,
)


class RankCascadeEngine:
    """
    Converts directional scores into
    simultaneous LONG and SHORT ranks.
    """

    def evaluate(
        self,
        *,
        asset: str,
        long_score: float,
        short_score: float,
    ) -> CandidateDualRank:

        long_rank = self._rank(
            long_score,
            "L",
        )

        short_rank = self._rank(
            short_score,
            "S",
        )

        state = self._state(
            long_score,
            short_score,
        )

        return CandidateDualRank(
            asset=asset,
            long_rank=long_rank,
            short_rank=short_rank,
            long_score=long_score,
            short_score=short_score,
            transition_state=state,
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
    def _state(
        long_score: float,
        short_score: float,
    ) -> str:

        if long_score > short_score + 15:
            return "LONG_DOMINANT"

        if short_score > long_score + 15:
            return "SHORT_DOMINANT"

        return "TRANSITION"


__all__ = [
    "RankCascadeEngine",
]
