from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_lifecycle import (
    EarlyBirdCandidateLifecycle,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)
from app.intelligence.early_bird.lifecycle_updater import (
    EarlyBirdLifecycleUpdater,
)
from app.intelligence.early_bird.rank_transition import (
    RankTransition,
)
from app.intelligence.early_bird.rank_transition_decision import (
    RankTransitionDecision,
)


NOW = datetime(
    2026,
    8,
    2,
    20,
    30,
    tzinfo=timezone.utc,
)


def test_behavior_promotion_updates_lifecycle_rank():

    lifecycle = EarlyBirdCandidateLifecycle(
        asset="HYPE",
        rank=CandidateRank.DISCOVERY,
        first_seen=NOW,
        last_seen=NOW,
        observations_count=5,
    )

    decision = RankTransitionDecision(
        asset="HYPE",
        previous_rank=CandidateRank.DISCOVERY,
        new_rank=CandidateRank.WATCHLIST,
        transition=RankTransition.PROMOTE,
        reason="accelerating behaviour detected",
        created_at=NOW,
    )

    updated = EarlyBirdLifecycleUpdater().apply(
        lifecycle,
        decision,
    )

    assert updated.rank == CandidateRank.WATCHLIST


def test_behavior_downgrade_updates_lifecycle_rank():

    lifecycle = EarlyBirdCandidateLifecycle(
        asset="SOL",
        rank=CandidateRank.PRIME,
        first_seen=NOW,
        last_seen=NOW,
        observations_count=10,
    )

    decision = RankTransitionDecision(
        asset="SOL",
        previous_rank=CandidateRank.PRIME,
        new_rank=CandidateRank.WATCHLIST,
        transition=RankTransition.DOWNGRADE,
        reason="critical behaviour decay detected",
        created_at=NOW,
    )

    updated = EarlyBirdLifecycleUpdater().apply(
        lifecycle,
        decision,
    )

    assert updated.rank == CandidateRank.WATCHLIST
