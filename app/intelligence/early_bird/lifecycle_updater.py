"""Early Bird lifecycle updater."""

from app.intelligence.early_bird.candidate_lifecycle import (
    EarlyBirdCandidateLifecycle,
)


class EarlyBirdLifecycleUpdater:
    """
    Applies lifecycle transition decisions.
    """

    def apply(
        self,
        lifecycle: EarlyBirdCandidateLifecycle,
        decision,
    ) -> EarlyBirdCandidateLifecycle:

        if lifecycle.asset != decision.asset:
            raise ValueError(
                "lifecycle and decision assets must match"
            )

        rank_history = lifecycle.rank_history

        if decision.new_rank != lifecycle.rank:
            rank_history = (
                rank_history
                + (decision.new_rank,)
            )

        return EarlyBirdCandidateLifecycle(
            asset=lifecycle.asset,
            rank=decision.new_rank,
            first_seen=lifecycle.first_seen,
            last_seen=decision.created_at,
            observations_count=lifecycle.observations_count,
            rank_history=rank_history,
            transition_history=(
                lifecycle.transition_history
                + (decision,)
            ),
        )


__all__ = [
    "EarlyBirdLifecycleUpdater",
]
