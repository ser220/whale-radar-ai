from app.intelligence.early_bird.candidate_memory import (
    CandidateMemory,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)
from app.intelligence.early_bird.candidate_reputation_calculator import (
    CandidateReputationCalculator,
)


def test_calculator_rewards_strong_candidate():

    memory = CandidateMemory(
        asset="HYPE",
        observations_count=150,
        promotion_count=3,
        downgrade_count=1,
        current_rank=CandidateRank.PRIME,
        highest_rank=CandidateRank.PRIME,
    )

    result = CandidateReputationCalculator().calculate(
        memory,
    )

    assert result.asset == "HYPE"
    assert result.score > 70
    assert result.stability_score > 50
    assert result.risk_score < 40


def test_calculator_penalizes_unstable_candidate():

    memory = CandidateMemory(
        asset="SOL",
        observations_count=20,
        promotion_count=0,
        downgrade_count=4,
        current_rank=CandidateRank.WATCHLIST,
        highest_rank=CandidateRank.WATCHLIST,
    )

    result = CandidateReputationCalculator().calculate(
        memory,
    )

    assert result.score < 50
    assert result.risk_score > 40


def test_prime_candidate_scores_above_discovery():

    prime = CandidateMemory(
        asset="HYPE",
        observations_count=100,
        promotion_count=2,
        downgrade_count=0,
        current_rank=CandidateRank.PRIME,
        highest_rank=CandidateRank.PRIME,
    )

    discovery = CandidateMemory(
        asset="BTC",
        observations_count=100,
        promotion_count=0,
        downgrade_count=0,
        current_rank=CandidateRank.DISCOVERY,
        highest_rank=CandidateRank.DISCOVERY,
    )

    calculator = CandidateReputationCalculator()

    assert (
        calculator.calculate(prime).score
        >
        calculator.calculate(discovery).score
    )
