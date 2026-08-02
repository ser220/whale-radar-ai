from app.intelligence.early_bird.candidate_dual_rank_lifecycle import (
    CandidateDualRankLifecycle,
)

from app.intelligence.early_bird.candidate_ranking_engine import (
    CandidateRankingEngine,
)


def test_reversal_candidate_gets_priority():

    lifecycle = CandidateDualRankLifecycle(
        asset="HYPE",
        current_long_rank="L2",
        current_short_rank="S4",
        highest_long_rank="L4",
        highest_short_rank="S4",
        current_state="REVERSAL_CONFIRMED",
        transition_history=(
            "PROMOTION",
            "REVERSAL",
        ),
    )

    result = CandidateRankingEngine().evaluate(
        lifecycle,
        confidence=90.0,
        risk_score=20.0,
    )

    assert result.direction == "REVERSAL"
    assert result.rank == "S4"
    assert result.priority > 90.0



def test_long_candidate_ranking():

    lifecycle = CandidateDualRankLifecycle(
        asset="SOL",
        current_long_rank="L4",
        current_short_rank="S1",
        highest_long_rank="L4",
        highest_short_rank="S1",
        current_state="LONG_DOMINANT",
        transition_history=(
            "PROMOTION",
        ),
    )

    result = CandidateRankingEngine().evaluate(
        lifecycle,
        confidence=85.0,
        risk_score=30.0,
    )

    assert result.direction == "LONG"
    assert result.rank == "L4"
    assert result.score > 80.0
