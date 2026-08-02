"""Rank transition detection engine."""

from datetime import datetime, timezone

from app.intelligence.early_bird.rank_transition_memory import (
    CandidateRankTransitionMemory,
)


class RankTransitionEngine:
    """
    Detects candidate evolution between
    two dual-rank states.
    """

    def evaluate(
        self,
        previous,
        current,
    ) -> CandidateRankTransitionMemory:

        transition = self._detect(
            previous,
            current,
        )

        return CandidateRankTransitionMemory(
            asset=current.asset,
            previous_rank=previous.long_rank,
            current_rank=current.short_rank
            if transition == "REVERSAL"
            else current.long_rank,
            transition_type=transition,
            reason=self._reason(
                transition
            ),
            timestamp=datetime.now(
                timezone.utc
            ),
        )

    @staticmethod
    def _detect(
        previous,
        current,
    ) -> str:

        if (
            previous.transition_state
            == "LONG_DOMINANT"
            and
            current.transition_state
            == "SHORT_DOMINANT"
        ):
            return "REVERSAL"

        if (
            current.long_score
            >
            previous.long_score
        ):
            return "PROMOTION"

        if (
            current.long_score
            <
            previous.long_score
        ):
            return "DEMOTION"

        return "STABLE"

    @staticmethod
    def _reason(
        transition: str,
    ) -> str:

        reasons = {
            "PROMOTION":
                "candidate strength increased",

            "DEMOTION":
                "candidate strength decreased",

            "REVERSAL":
                "directional dominance changed",

            "STABLE":
                "no meaningful rank movement",
        }

        return reasons[
            transition
        ]


__all__ = [
    "RankTransitionEngine",
]
