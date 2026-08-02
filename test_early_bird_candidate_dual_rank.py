from app.intelligence.early_bird.candidate_dual_rank import (
    CandidateDualRank,
)


def test_dual_rank_contract():

    rank = CandidateDualRank(
        asset="HYPE",
        long_rank="L3",
        short_rank="S1",
        long_score=78.0,
        short_score=25.0,
        transition_state="LONG_DOMINANT",
    )

    assert rank.asset == "HYPE"
    assert rank.long_rank == "L3"
    assert rank.short_rank == "S1"
    assert rank.long_score == 78.0
    assert rank.short_score == 25.0
    assert (
        rank.transition_state
        ==
        "LONG_DOMINANT"
    )


def test_dual_rank_rejects_invalid_score():

    try:
        CandidateDualRank(
            asset="BTC",
            long_rank="L1",
            short_rank="S1",
            long_score=120.0,
            short_score=50.0,
            transition_state="NEUTRAL",
        )

    except ValueError as exc:
        assert "score" in str(exc)

    else:
        raise AssertionError(
            "Expected ValueError"
        )
