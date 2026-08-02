from app.intelligence.early_bird.candidate_dual_rank import (
    CandidateDualRank,
)

from app.intelligence.early_bird.rank_transition_engine import (
    RankTransitionEngine,
)


def test_detects_long_promotion():

    previous = CandidateDualRank(
        asset="HYPE",
        long_rank="L2",
        short_rank="S1",
        long_score=55.0,
        short_score=20.0,
        transition_state="LONG_DOMINANT",
    )

    current = CandidateDualRank(
        asset="HYPE",
        long_rank="L3",
        short_rank="S1",
        long_score=70.0,
        short_score=25.0,
        transition_state="LONG_DOMINANT",
    )

    result = RankTransitionEngine().evaluate(
        previous,
        current,
    )

    assert result.transition_type == "PROMOTION"



def test_detects_reversal():

    previous = CandidateDualRank(
        asset="HYPE",
        long_rank="L4",
        short_rank="S1",
        long_score=85.0,
        short_score=20.0,
        transition_state="LONG_DOMINANT",
    )

    current = CandidateDualRank(
        asset="HYPE",
        long_rank="L2",
        short_rank="S4",
        long_score=55.0,
        short_score=85.0,
        transition_state="SHORT_DOMINANT",
    )

    result = RankTransitionEngine().evaluate(
        previous,
        current,
    )

    assert result.transition_type == "REVERSAL"



def test_detects_stable():

    rank = CandidateDualRank(
        asset="BTC",
        long_rank="L3",
        short_rank="S2",
        long_score=65.0,
        short_score=50.0,
        transition_state="LONG_DOMINANT",
    )

    result = RankTransitionEngine().evaluate(
        rank,
        rank,
    )

    assert result.transition_type == "STABLE"
