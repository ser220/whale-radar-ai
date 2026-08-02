from app.intelligence.early_bird.candidate_reputation_score import (
    CandidateReputationScore,
)


def test_candidate_reputation_score_contract():

    reputation = CandidateReputationScore(
        asset="HYPE",
        score=87.0,
        stability_score=90.0,
        promotion_quality=85.0,
        risk_score=15.0,
    )

    assert reputation.asset == "HYPE"
    assert reputation.score == 87.0
    assert reputation.stability_score == 90.0
    assert reputation.promotion_quality == 85.0
    assert reputation.risk_score == 15.0


def test_reputation_score_rejects_invalid_score():

    try:
        CandidateReputationScore(
            asset="BTC",
            score=120.0,
            stability_score=50.0,
            promotion_quality=50.0,
            risk_score=20.0,
        )
    except ValueError as exc:
        assert "score" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_reputation_score_rejects_empty_asset():

    try:
        CandidateReputationScore(
            asset="",
            score=50.0,
            stability_score=50.0,
            promotion_quality=50.0,
            risk_score=20.0,
        )
    except ValueError as exc:
        assert "asset" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
