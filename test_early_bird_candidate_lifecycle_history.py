from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_lifecycle import (
    EarlyBirdCandidateLifecycle,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)


NOW = datetime(
    2026,
    8,
    2,
    16,
    0,
    tzinfo=timezone.utc,
)


def test_lifecycle_stores_rank_history():
    lifecycle = EarlyBirdCandidateLifecycle(
        asset="HYPE",
        rank=CandidateRank.WATCHLIST,
        first_seen=NOW,
        last_seen=NOW,
        observations_count=5,
        rank_history=(
            CandidateRank.DISCOVERY,
            CandidateRank.WATCHLIST,
        ),
    )

    assert lifecycle.rank_history == (
        CandidateRank.DISCOVERY,
        CandidateRank.WATCHLIST,
    )


def test_rank_history_defaults_to_current_rank():
    lifecycle = EarlyBirdCandidateLifecycle(
        asset="BTC",
        rank=CandidateRank.DISCOVERY,
        first_seen=NOW,
        last_seen=NOW,
    )

    assert lifecycle.rank_history == (
        CandidateRank.DISCOVERY,
    )
