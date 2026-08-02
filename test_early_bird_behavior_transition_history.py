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
    21,
    0,
    tzinfo=timezone.utc,
)


def test_behavior_transition_keeps_rank_history():

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

    assert updated.rank_history == (
        CandidateRank.DISCOVERY,
        CandidateRank.WATCHLIST,
    )
