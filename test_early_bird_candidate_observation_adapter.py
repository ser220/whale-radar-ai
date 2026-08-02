from datetime import datetime, timezone
from types import SimpleNamespace

from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)
from app.intelligence.early_bird.candidate_observation_adapter import (
    build_candidate_observation,
)


NOW = datetime(
    2026,
    8,
    2,
    18,
    15,
    tzinfo=timezone.utc,
)


def test_candidate_is_converted_to_observation():
    candidate = SimpleNamespace(
        asset="HYPE",
        observed_at=NOW,
        quality=82.5,
        whale_activity_score=70.0,
        open_interest_change_score=88.0,
        funding_divergence_score=61.0,
        volume_expansion_score=76.0,
        relative_strength_score=74.0,
        liquidity_event_score=0.0,
        structure_event_score=68.0,
        momentum_shift_score=79.0,
        freshness_score=95.0,
        data_completeness_score=90.0,
    )

    observation = build_candidate_observation(
        candidate
    )

    assert isinstance(
        observation,
        EarlyBirdCandidateObservation,
    )
    assert observation.asset == "HYPE"
    assert observation.observed_at == NOW
    assert observation.open_interest_change_score == 88.0
