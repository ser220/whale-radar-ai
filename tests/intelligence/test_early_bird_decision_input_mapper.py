from datetime import datetime, timezone

import pytest

from app.intelligence.early_bird.models import (
    EarlyBirdCandidate,
)

from app.intelligence.candidate_decision_input.early_bird_mapper import (
    EarlyBirdDecisionInputMapper,
)

from app.intelligence.candidate_decision_input import (
    CandidateDecisionInputStatus,
    CandidateDecisionInputVersion,
)


def build_candidate() -> EarlyBirdCandidate:
    return EarlyBirdCandidate(
        candidate_id="candidate-001",
        asset="BTC",
        observed_at=datetime.now(
            timezone.utc
        ),
        source="early_bird_test",
        quality=80,
        whale_activity_score=70,
        open_interest_change_score=60,
        funding_divergence_score=50,
        volume_expansion_score=75,
        relative_strength_score=65,
        liquidity_event_score=40,
        structure_event_score=55,
        momentum_shift_score=70,
        freshness_score=90,
        data_completeness_score=95,
        fast_event_ids=("event-001",),
        observation_ids=("obs-001",),
        metadata={},
    )


def test_early_bird_candidate_maps_to_candidate_input():
    candidate = build_candidate()

    projection = (
        EarlyBirdDecisionInputMapper()
        .from_candidate(candidate)
    )

    assert (
        projection.candidate_reference
        == "candidate-001"
    )

    assert (
        projection.intelligence_reference
        == "early_bird:candidate-001"
    )

    assert (
        projection.status
        == CandidateDecisionInputStatus.AVAILABLE
    )

    assert (
        projection.version
        == CandidateDecisionInputVersion.V1
    )


def test_mapper_preserves_timestamp():
    candidate = build_candidate()

    projection = (
        EarlyBirdDecisionInputMapper()
        .from_candidate(candidate)
    )

    assert (
        projection.created_at
        == candidate.observed_at
    )


def test_invalid_candidate_rejected():
    with pytest.raises(TypeError):
        EarlyBirdDecisionInputMapper().from_candidate(
            "invalid"
        )
