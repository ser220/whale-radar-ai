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


def test_discovery_promotes_after_confirmations():

    lifecycle = EarlyBirdCandidateLifecycle(
        asset="HYPE",
        rank=CandidateRank.DISCOVERY,
        first_seen=NOW,
        last_seen=NOW,
        observations_count=5,
    )

    decision = EarlyBirdRankTransitionPolicy().evaluate(
        lifecycle=lifecycle,
        observation={
            "negative_events": 0,
        },
    )

    assert decision.transition == (
        RankTransition.PROMOTE
    )

    assert decision.new_rank == (
        CandidateRank.WATCHLIST
    )


def test_prime_downgrades_after_negative_events():

    lifecycle = EarlyBirdCandidateLifecycle(
        asset="BTC",
        rank=CandidateRank.PRIME,
        first_seen=NOW,
        last_seen=NOW,
        observations_count=10,
    )

    decision = EarlyBirdRankTransitionPolicy().evaluate(
        lifecycle=lifecycle,
        observation={
            "negative_events": 3,
        },
    )

    assert decision.transition == (
        RankTransition.DOWNGRADE
    )

    assert decision.new_rank == (
        CandidateRank.WATCHLIST
    )
