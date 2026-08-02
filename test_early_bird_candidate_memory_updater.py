from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_memory import (
    CandidateMemory,
)
from app.intelligence.early_bird.candidate_memory_updater import (
    CandidateMemoryUpdater,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
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
    30,
    tzinfo=timezone.utc,
)


def test_memory_updater_counts_promotion():

    memory = CandidateMemory(
        asset="HYPE",
        observations_count=50,
        promotion_count=0,
        downgrade_count=0,
        current_rank=CandidateRank.DISCOVERY,
        highest_rank=CandidateRank.DISCOVERY,
    )

    decision = RankTransitionDecision(
        asset="HYPE",
        previous_rank=CandidateRank.DISCOVERY,
        new_rank=CandidateRank.WATCHLIST,
        transition=RankTransition.PROMOTE,
        reason="promotion",
        created_at=NOW,
    )

    updated = CandidateMemoryUpdater().apply(
        memory,
        decision,
    )

    assert updated.promotion_count == 1
    assert updated.current_rank == CandidateRank.WATCHLIST
    assert updated.highest_rank == CandidateRank.WATCHLIST


def test_memory_updater_preserves_highest_rank_on_downgrade():

    memory = CandidateMemory(
        asset="HYPE",
        observations_count=150,
        promotion_count=3,
        downgrade_count=0,
        current_rank=CandidateRank.PRIME,
        highest_rank=CandidateRank.PRIME,
    )

    decision = RankTransitionDecision(
        asset="HYPE",
        previous_rank=CandidateRank.PRIME,
        new_rank=CandidateRank.WATCHLIST,
        transition=RankTransition.DOWNGRADE,
        reason="critical behaviour decay",
        created_at=NOW,
    )

    updated = CandidateMemoryUpdater().apply(
        memory,
        decision,
    )

    assert updated.downgrade_count == 1
    assert updated.current_rank == CandidateRank.WATCHLIST
    assert updated.highest_rank == CandidateRank.PRIME
