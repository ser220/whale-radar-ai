from app.intelligence.early_bird.candidate_behavior_policy import (
    CandidateBehaviorPolicy,
)
from app.intelligence.early_bird.candidate_behavior_score import (
    CandidateBehaviorScore,
)


def test_strengthening_behavior_is_accelerating():

    score = CandidateBehaviorScore(
        asset="HYPE",
        behavior_direction="strengthening",
        strength_score=85.0,
        decay_score=0.0,
        confidence=90.0,
    )

    result = CandidateBehaviorPolicy().evaluate(
        score,
    )

    assert result.state == "accelerating"
    assert result.priority == "high"
    assert result.action_hint == "promote_ready"


def test_small_decay_is_warning():

    score = CandidateBehaviorScore(
        asset="BTC",
        behavior_direction="weakening",
        strength_score=20.0,
        decay_score=25.0,
        confidence=70.0,
    )

    result = CandidateBehaviorPolicy().evaluate(
        score,
    )

    assert result.state == "degrading"
    assert result.priority == "medium"
    assert result.action_hint == "monitor"


def test_large_decay_is_critical():

    score = CandidateBehaviorScore(
        asset="SOL",
        behavior_direction="weakening",
        strength_score=10.0,
        decay_score=80.0,
        confidence=90.0,
    )

    result = CandidateBehaviorPolicy().evaluate(
        score,
    )

    assert result.state == "critical"
    assert result.priority == "high"
    assert result.action_hint == "downgrade_check"
