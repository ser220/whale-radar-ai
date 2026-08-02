from app.intelligence.early_bird.candidate_memory import (
    CandidateMemory,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)
from app.intelligence.early_bird.candidate_reputation_calculator import (
    CandidateReputationCalculator,
)
from app.intelligence.early_bird.candidate_selector import (
    CandidateSelector,
)


def test_selector_accepts_high_quality_prime():

    memory = CandidateMemory(
        asset="HYPE",
        observations_count=150,
        promotion_count=3,
        downgrade_count=1,
        current_rank=CandidateRank.PRIME,
        highest_rank=CandidateRank.PRIME,
    )

    reputation = CandidateReputationCalculator().calculate(
        memory
    )

    result = CandidateSelector().select(
        memory,
        reputation,
    )

    assert result is not None
    assert result.asset == "HYPE"
    assert result.rank == CandidateRank.PRIME


def test_selector_rejects_weak_candidate():

    memory = CandidateMemory(
        asset="DOGE",
        observations_count=10,
        promotion_count=0,
        downgrade_count=4,
        current_rank=CandidateRank.DISCOVERY,
        highest_rank=CandidateRank.DISCOVERY,
    )

    reputation = CandidateReputationCalculator().calculate(
        memory
    )

    result = CandidateSelector().select(
        memory,
        reputation,
    )

    assert result is None
