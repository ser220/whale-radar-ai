"""Candidate selection engine."""

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)

from app.intelligence.early_bird.candidate_selection_result import (
    CandidateSelectionResult,
)


class CandidateSelector:
    """
    Selects candidates based on lifecycle rank
    and reputation quality.
    """

    def select(
        self,
        memory,
        reputation,
    ):

        if (
            reputation.asset
            != memory.asset
        ):
            raise ValueError(
                "memory and reputation asset mismatch"
            )

        if (
            memory.current_rank
            == CandidateRank.PRIME
            and reputation.score >= 70
        ):
            return CandidateSelectionResult(
                asset=memory.asset,
                rank=memory.current_rank,
                reputation_score=reputation.score,
                selection_reason=(
                    "prime candidate with strong reputation"
                ),
            )

        if (
            memory.current_rank
            == CandidateRank.WATCHLIST
            and reputation.score >= 80
        ):
            return CandidateSelectionResult(
                asset=memory.asset,
                rank=memory.current_rank,
                reputation_score=reputation.score,
                selection_reason=(
                    "watchlist candidate with strong reputation"
                ),
            )

        return None


__all__ = [
    "CandidateSelector",
]
