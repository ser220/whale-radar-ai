from datetime import datetime, timezone

import pytest

from app.intelligence.early_bird.rank_transition import (
    RankTransition,
)

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)

from app.intelligence.early_bird.rank_transition_decision import (
    RankTransitionDecision,
)


NOW = datetime(
    2026,
    8,
    2,
    14,
    0,
    tzinfo=timezone.utc,
)


def test_transition_decision_contract():
    decision = RankTransitionDecision(
        asset="HYPE",
        previous_rank=CandidateRank.DISCOVERY,
        new_rank=CandidateRank.WATCHLIST,
        transition=RankTransition.PROMOTE,
        reason="5 confirmations",
        created_at=NOW,
    )

    assert decision.asset == "HYPE"
    assert decision.transition == RankTransition.PROMOTE
    assert decision.previous_rank == CandidateRank.DISCOVERY


def test_reason_cannot_be_empty():
    with pytest.raises(
        ValueError,
        match="reason must not be empty",
    ):
        RankTransitionDecision(
            asset="BTC",
            previous_rank=CandidateRank.DISCOVERY,
            new_rank=CandidateRank.WATCHLIST,
            transition=RankTransition.PROMOTE,
            reason="",
            created_at=NOW,
        )
