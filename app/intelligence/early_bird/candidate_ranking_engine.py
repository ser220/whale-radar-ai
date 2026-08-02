"""Candidate ranking engine."""

from app.intelligence.early_bird.candidate_ranking_record import (
    CandidateRankingRecord,
)


RANK_WEIGHTS = {
    "L4": 90.0,
    "S4": 90.0,
    "L3": 75.0,
    "S3": 75.0,
    "L2": 55.0,
    "S2": 55.0,
    "L1": 35.0,
    "S1": 35.0,
}


class CandidateRankingEngine:
    """
    Converts candidate lifecycle state
    into ranking records.
    """

    def evaluate(
        self,
        lifecycle,
        *,
        confidence: float,
        risk_score: float,
    ) -> CandidateRankingRecord:

        direction = self._direction(
            lifecycle
        )

        rank = self._rank(
            lifecycle,
            direction,
        )

        base_score = RANK_WEIGHTS.get(
            rank,
            0.0,
        )

        priority = self._priority(
            lifecycle,
            base_score,
        )

        score = min(
            100.0,
            (
                base_score * 0.6
                +
                confidence * 0.4
            ),
        )

        return CandidateRankingRecord(
            asset=lifecycle.asset,
            direction=direction,
            rank=rank,
            score=score,
            confidence=confidence,
            risk_score=risk_score,
            priority=priority,
        )

    @staticmethod
    def _direction(
        lifecycle,
    ) -> str:

        if (
            lifecycle.current_state
            ==
            "REVERSAL_CONFIRMED"
        ):
            return "REVERSAL"

        if (
            lifecycle.current_state
            ==
            "SHORT_DOMINANT"
        ):
            return "SHORT"

        return "LONG"

    @staticmethod
    def _rank(
        lifecycle,
        direction,
    ) -> str:

        if direction == "SHORT":
            return lifecycle.current_short_rank

        if direction == "REVERSAL":
            return lifecycle.current_short_rank

        return lifecycle.current_long_rank

    @staticmethod
    def _priority(
        lifecycle,
        score,
    ) -> float:

        priority = score

        if (
            lifecycle.current_state
            ==
            "REVERSAL_CONFIRMED"
            and
            lifecycle.highest_long_rank
            ==
            "L4"
            and
            lifecycle.current_short_rank
            in ("S3", "S4")
        ):
            priority += 15.0

        return min(
            100.0,
            priority,
        )


__all__ = [
    "CandidateRankingEngine",
]
