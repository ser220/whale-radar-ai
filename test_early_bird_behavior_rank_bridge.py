from app.intelligence.early_bird.candidate_behavior_policy import (
    CandidateBehaviorPolicy,
)
from app.intelligence.early_bird.candidate_behavior_score import (
    CandidateBehaviorScore,
)
from app.intelligence.early_bird.candidate_rank import (
    CandidateRank,
)


def test_accelerating_candidate_is_ready_for_promotion():

    score = CandidateBehaviorScore(
        asset="HYPE",
        behavior_direction="strengthening",
        strength_score=85.0,
        decay_score=0.0,
        confidence=90.0,
    )

    assessment = CandidateBehaviorPolicy().evaluate(
        score,
    )

    assert assessment.action_hint == "promote_ready"


def test_critical_candidate_requires_downgrade_check():

    score = CandidateBehaviorScore(
        asset="SOL",
        behavior_direction="weakening",
        strength_score=10.0,
        decay_score=85.0,
        confidence=90.0,
    )

    assessment = CandidateBehaviorPolicy().evaluate(
        score,
    )

    assert assessment.action_hint == "downgrade_check"
