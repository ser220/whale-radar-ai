"""Candidate reputation calculator."""

from app.intelligence.early_bird.candidate_memory import (
    CandidateMemory,
)

from app.intelligence.early_bird.candidate_reputation_score import (
    CandidateReputationScore,
)


class CandidateReputationCalculator:
    """
    Calculates long-term candidate reputation
    from accumulated memory.
    """

    def calculate(
        self,
        memory: CandidateMemory,
    ) -> CandidateReputationScore:

        if not isinstance(
            memory,
            CandidateMemory,
        ):
            raise TypeError(
                "memory must be CandidateMemory"
            )

        stability_score = self._stability(
            memory,
        )

        promotion_quality = self._promotion_quality(
            memory,
        )

        risk_score = self._risk(
            memory,
        )

        rank_bonus = self._rank_bonus(
            memory,
        )

        score = (
            stability_score * 0.4
            + promotion_quality * 0.35
            + rank_bonus * 0.25
            - risk_score * 0.15
        )

        score = max(
            0.0,
            min(
                100.0,
                score,
            ),
        )

        return CandidateReputationScore(
            asset=memory.asset,
            score=round(score, 2),
            stability_score=round(
                stability_score,
                2,
            ),
            promotion_quality=round(
                promotion_quality,
                2,
            ),
            risk_score=round(
                risk_score,
                2,
            ),
        )

    @staticmethod
    def _stability(
        memory: CandidateMemory,
    ) -> float:

        if memory.observations_count >= 100:
            return 90.0

        if memory.observations_count >= 50:
            return 70.0

        return 40.0

    @staticmethod
    def _promotion_quality(
        memory: CandidateMemory,
    ) -> float:

        return min(
            100.0,
            memory.promotion_count * 30.0,
        )

    @staticmethod
    def _risk(
        memory: CandidateMemory,
    ) -> float:

        return min(
            100.0,
            memory.downgrade_count * 20.0,
        )

    @staticmethod
    def _rank_bonus(
        memory: CandidateMemory,
    ) -> float:

        bonuses = {
            "discovery": 30.0,
            "watchlist": 60.0,
            "prime": 100.0,
        }

        return bonuses[
            memory.highest_rank.value
        ]


__all__ = [
    "CandidateReputationCalculator",
]
