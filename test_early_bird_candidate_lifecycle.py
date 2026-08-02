from datetime import datetime, timezone

import pytest

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
    12,
    0,
    tzinfo=timezone.utc,
)


def test_initial_candidate_lifecycle():
    state = EarlyBirdCandidateLifecycle(
        asset="HYPE",
        rank=CandidateRank.DISCOVERY,
        first_seen=NOW,
        last_seen=NOW,
    )

    assert state.asset == "HYPE"
    assert state.rank == CandidateRank.DISCOVERY
    assert state.observations_count == 0


def test_asset_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="asset must not be empty",
    ):
        EarlyBirdCandidateLifecycle(
            asset="",
            rank=CandidateRank.DISCOVERY,
            first_seen=NOW,
            last_seen=NOW,
        )
