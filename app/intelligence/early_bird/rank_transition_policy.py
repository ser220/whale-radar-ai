"""Early Bird candidate rank transition policy."""

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)

from app.intelligence.early_bird.rank_transition import (
    RankTransition,
)

from app.intelligence.early_bird.rank_transition_decision import (
    RankTransitionDecision,
)


class EarlyBirdRankTransitionPolicy:
    """
    Decides lifecycle rank movement using
    candidate state and current observation.
    """

    def evaluate(
        self,
        *,
        lifecycle,
        observation,
        behavior_assessment=None,
    ) -> RankTransitionDecision:

        if behavior_assessment is not None:

            if (
                behavior_assessment.action_hint
                == "promote_ready"
                and lifecycle.rank
                == CandidateRank.DISCOVERY
            ):
                return RankTransitionDecision(
                    asset=lifecycle.asset,
                    previous_rank=lifecycle.rank,
                    new_rank=CandidateRank.WATCHLIST,
                    transition=RankTransition.PROMOTE,
                    reason=(
                        "accelerating behaviour detected"
                    ),
                    created_at=self._now(),
                )

            if (
                behavior_assessment.action_hint
                == "downgrade_check"
                and lifecycle.rank
                == CandidateRank.PRIME
            ):
                return RankTransitionDecision(
                    asset=lifecycle.asset,
                    previous_rank=lifecycle.rank,
                    new_rank=CandidateRank.WATCHLIST,
                    transition=RankTransition.DOWNGRADE,
                    reason=(
                        "critical behaviour decay detected"
                    ),
                    created_at=self._now(),
                )

        negative_events = int(
            observation.get(
                "negative_events",
                0,
            )
        )

        if (
            lifecycle.rank == CandidateRank.DISCOVERY
            and lifecycle.observations_count >= 5
            and negative_events == 0
        ):
            return RankTransitionDecision(
                asset=lifecycle.asset,
                previous_rank=lifecycle.rank,
                new_rank=CandidateRank.WATCHLIST,
                transition=RankTransition.PROMOTE,
                reason=(
                    "confirmation threshold reached"
                ),
                created_at=self._now(),
            )

        if (
            lifecycle.rank == CandidateRank.PRIME
            and negative_events >= 3
        ):
            return RankTransitionDecision(
                asset=lifecycle.asset,
                previous_rank=lifecycle.rank,
                new_rank=CandidateRank.WATCHLIST,
                transition=RankTransition.DOWNGRADE,
                reason=(
                    "negative behaviour detected"
                ),
                created_at=self._now(),
            )

        return RankTransitionDecision(
            asset=lifecycle.asset,
            previous_rank=lifecycle.rank,
            new_rank=lifecycle.rank,
            transition=RankTransition.HOLD,
            reason=(
                "no transition criteria met"
            ),
            created_at=self._now(),
        )

    @staticmethod
    def _now():
        from datetime import datetime, timezone

        return datetime.now(
            timezone.utc
        )


__all__ = [
    "EarlyBirdRankTransitionPolicy",
]
