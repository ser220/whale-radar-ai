"""Candidate memory updater."""

from app.intelligence.early_bird.candidate_memory import (
    CandidateMemory,
)

from app.intelligence.early_bird.rank_transition import (
    RankTransition,
)


class CandidateMemoryUpdater:
    """
    Applies rank transition decisions
    to candidate long-term memory.
    """

    def apply(
        self,
        memory: CandidateMemory,
        decision,
    ) -> CandidateMemory:

        if not isinstance(
            memory,
            CandidateMemory,
        ):
            raise TypeError(
                "memory must be CandidateMemory"
            )

        if decision.transition == RankTransition.PROMOTE:

            highest_rank = self._highest_rank(
                memory.highest_rank,
                decision.new_rank,
            )

            return CandidateMemory(
                asset=memory.asset,
                observations_count=(
                    memory.observations_count
                ),
                promotion_count=(
                    memory.promotion_count + 1
                ),
                downgrade_count=(
                    memory.downgrade_count
                ),
                current_rank=decision.new_rank,
                highest_rank=highest_rank,
            )

        if decision.transition == RankTransition.DOWNGRADE:

            return CandidateMemory(
                asset=memory.asset,
                observations_count=(
                    memory.observations_count
                ),
                promotion_count=(
                    memory.promotion_count
                ),
                downgrade_count=(
                    memory.downgrade_count + 1
                ),
                current_rank=decision.new_rank,
                highest_rank=memory.highest_rank,
            )

        return memory

    @staticmethod
    def _highest_rank(
        current,
        candidate,
    ):
        order = {
            "discovery": 0,
            "watchlist": 1,
            "prime": 2,
        }

        if (
            order[candidate.value]
            > order[current.value]
        ):
            return candidate

        return current


__all__ = [
    "CandidateMemoryUpdater",
]
