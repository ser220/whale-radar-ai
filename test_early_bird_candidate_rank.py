import pytest

from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)


def test_candidate_rank_values_exist():
    assert CandidateRank.DISCOVERY.value == "discovery"
    assert CandidateRank.WATCHLIST.value == "watchlist"
    assert CandidateRank.PRIME.value == "prime"
    assert CandidateRank.ACTIONABLE.value == "actionable"


def test_candidate_rank_rejects_unknown():
    with pytest.raises(ValueError):
        CandidateRank("unknown")
