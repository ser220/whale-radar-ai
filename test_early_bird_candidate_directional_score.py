from app.intelligence.early_bird.candidate_directional_score import (
    CandidateDirectionalScore,
)


def test_directional_score_contract():

    score = CandidateDirectionalScore(
        asset="HYPE",
        long_score=84.0,
        short_score=72.0,
        long_rank="L3",
        short_rank="S2",
        market_regime="bullish_exhaustion",
        confidence=88.0,
    )

    assert score.asset == "HYPE"
    assert score.long_score == 84.0
    assert score.short_score == 72.0
    assert score.long_rank == "L3"
    assert score.short_rank == "S2"
    assert (
        score.market_regime
        ==
        "bullish_exhaustion"
    )


def test_directional_score_rejects_invalid_score():

    try:
        CandidateDirectionalScore(
            asset="BTC",
            long_score=120.0,
            short_score=50.0,
            long_rank="L1",
            short_rank="S1",
            market_regime="neutral",
            confidence=50.0,
        )
    except ValueError as exc:
        assert "score" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
