"""Dual rank lifecycle updater."""

from app.intelligence.early_bird.candidate_dual_rank_lifecycle import (
    CandidateDualRankLifecycle,
)


class DualRankLifecycleUpdater:
    """
    Updates candidate lifecycle from new dual rank state.
    """

    def update(
        self,
        lifecycle,
        new_rank,
    ) -> CandidateDualRankLifecycle:

        transition_history = list(
            lifecycle.transition_history
        )

        state = self._resolve_state(
            lifecycle,
            new_rank,
        )

        transition = self._resolve_transition(
            lifecycle,
            new_rank,
            state,
        )

        if transition not in transition_history:
            transition_history.append(
                transition
            )

        highest_long_rank = self._max_long_rank(
            lifecycle.highest_long_rank,
            new_rank.long_rank,
        )

        highest_short_rank = self._max_short_rank(
            lifecycle.highest_short_rank,
            new_rank.short_rank,
        )

        return CandidateDualRankLifecycle(
            asset=new_rank.asset,
            current_long_rank=new_rank.long_rank,
            current_short_rank=new_rank.short_rank,
            highest_long_rank=highest_long_rank,
            highest_short_rank=highest_short_rank,
            current_state=state,
            transition_history=tuple(
                transition_history
            ),
        )

    @staticmethod
    def _resolve_state(
        lifecycle,
        new_rank,
    ) -> str:

        if (
            lifecycle.current_state
            == "LONG_DOMINANT"
            and
            new_rank.transition_state
            == "SHORT_DOMINANT"
        ):
            return "REVERSAL_CONFIRMED"

        return new_rank.transition_state

    @staticmethod
    def _resolve_transition(
        lifecycle,
        new_rank,
        state,
    ) -> str:

        if state == "REVERSAL_CONFIRMED":
            return "REVERSAL"

        if (
            new_rank.long_rank
            >
            lifecycle.current_long_rank
        ):
            return "PROMOTION"

        if (
            new_rank.long_rank
            <
            lifecycle.current_long_rank
        ):
            return "DEMOTION"

        return "STABLE"

    @staticmethod
    def _max_long_rank(
        old_rank,
        new_rank,
    ):

        return max(
            old_rank,
            new_rank,
        )

    @staticmethod
    def _max_short_rank(
        old_rank,
        new_rank,
    ):

        return max(
            old_rank,
            new_rank,
        )


__all__ = [
    "DualRankLifecycleUpdater",
]
