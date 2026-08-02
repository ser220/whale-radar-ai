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

from app.intelligence.early_bird.rank_transition_decision import (
    RankTransitionDecision,
)

from app.intelligence.early_bird.lifecycle_updater import (
    EarlyBirdLifecycleUpdater,
)


NOW = datetime(
    2026,
    8,
    2,
    16,
    0,
    tzinfo=timezone.utc,
)


def test_promote_updates_candidate_rank():

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
        reason="confirmed",
        created_at=NOW,
    )

    updated = EarlyBirdLifecycleUpdater().apply(
        lifecycle,
        decision,
    )

    assert updated.rank == CandidateRank.WATCHLIST
    assert updated.asset == "HYPE"


def test_updater_appends_new_rank_to_history():

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
        reason="confirmed",
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
