from app.intelligence.early_bird.candidate_memory import (
    CandidateMemory,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)


def test_candidate_memory_contract():

    memory = CandidateMemory(
        asset="HYPE",
        observations_count=150,
        promotion_count=3,
        downgrade_count=1,
        current_rank=CandidateRank.PRIME,
        highest_rank=CandidateRank.PRIME,
    )

    assert memory.asset == "HYPE"
    assert memory.observations_count == 150
    assert memory.promotion_count == 3
    assert memory.downgrade_count == 1
    assert memory.current_rank == CandidateRank.PRIME
    assert memory.highest_rank == CandidateRank.PRIME


def test_candidate_memory_rejects_empty_asset():

    try:
        CandidateMemory(
            asset="",
            observations_count=0,
            promotion_count=0,
            downgrade_count=0,
            current_rank=CandidateRank.DISCOVERY,
            highest_rank=CandidateRank.DISCOVERY,
        )
    except ValueError as exc:
        assert "asset" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_candidate_memory_rejects_negative_counts():

    try:
        CandidateMemory(
            asset="BTC",
            observations_count=-1,
            promotion_count=0,
            downgrade_count=0,
            current_rank=CandidateRank.DISCOVERY,
            highest_rank=CandidateRank.DISCOVERY,
        )
    except ValueError as exc:
        assert "count" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
