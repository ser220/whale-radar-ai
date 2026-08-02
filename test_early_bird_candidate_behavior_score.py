from app.intelligence.early_bird.candidate_behavior_score import (
    CandidateBehaviorScore,
)


def test_behavior_score_contract():

    score = CandidateBehaviorScore(
        asset="HYPE",
        behavior_direction="strengthening",
        strength_score=85.0,
        decay_score=5.0,
        confidence=90.0,
    )

    assert score.asset == "HYPE"
    assert score.behavior_direction == "strengthening"
    assert score.strength_score == 85.0
    assert score.decay_score == 5.0
    assert score.confidence == 90.0


def test_behavior_score_rejects_invalid_strength():

    try:
        CandidateBehaviorScore(
            asset="BTC",
            behavior_direction="strengthening",
            strength_score=120.0,
            decay_score=0.0,
            confidence=80.0,
        )
    except ValueError as exc:
        assert "strength_score" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )


def test_behavior_score_rejects_empty_asset():

    try:
        CandidateBehaviorScore(
            asset="",
            behavior_direction="stable",
            strength_score=50.0,
            decay_score=0.0,
            confidence=50.0,
        )
    except ValueError as exc:
        assert "asset" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError"
        )
