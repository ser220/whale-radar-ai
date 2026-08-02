from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)

from app.intelligence.early_bird.candidate_lifecycle import (
    EarlyBirdCandidateLifecycle,
)

from app.intelligence.early_bird.rank_transition import (
    RankTransition,
)

from app.intelligence.early_bird.rank_transition_policy import (
    EarlyBirdRankTransitionPolicy,
)


NOW = datetime(
    2026,
    8,
    2,
    15,
    0,
    tzinfo=timezone.utc,
)


def test_policy_uses_lifecycle_context():

    lifecycle = EarlyBirdCandidateLifecycle(
        asset="HYPE",
        rank=CandidateRank.DISCOVERY,
        first_seen=NOW,
        last_seen=NOW,
        observations_count=5,
    )

    policy = EarlyBirdRankTransitionPolicy()

    decision = policy.evaluate(
        lifecycle=lifecycle,
        observation={
            "negative_events": 0,
        },
    )

    assert decision.asset == "HYPE"

    assert decision.transition == (
        RankTransition.PROMOTE
    )

    assert decision.new_rank == (
        CandidateRank.WATCHLIST
    )
