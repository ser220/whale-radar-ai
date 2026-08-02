from datetime import datetime, timezone

import pytest

from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)


NOW = datetime(
    2026,
    8,
    2,
    18,
    0,
    tzinfo=timezone.utc,
)


def test_candidate_observation_contract():
    observation = EarlyBirdCandidateObservation(
        asset="hype",
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

    assert observation.asset == "HYPE"
    assert observation.observed_at == NOW
    assert observation.quality == 82.5
    assert observation.open_interest_change_score == 88.0


def test_observation_requires_timezone_aware_datetime():
    with pytest.raises(
        ValueError,
        match="observed_at must be timezone aware",
    ):
        EarlyBirdCandidateObservation(
            asset="BTC",
            observed_at=datetime(
                2026,
                8,
                2,
                18,
                0,
            ),
            quality=80.0,
            whale_activity_score=70.0,
            open_interest_change_score=75.0,
            funding_divergence_score=60.0,
            volume_expansion_score=72.0,
            relative_strength_score=65.0,
            liquidity_event_score=0.0,
            structure_event_score=68.0,
            momentum_shift_score=71.0,
            freshness_score=90.0,
            data_completeness_score=85.0,
        )


def test_observation_rejects_score_above_100():
    with pytest.raises(
        ValueError,
        match="quality must be between 0 and 100",
    ):
        EarlyBirdCandidateObservation(
            asset="BTC",
            observed_at=NOW,
            quality=101.0,
            whale_activity_score=70.0,
            open_interest_change_score=75.0,
            funding_divergence_score=60.0,
            volume_expansion_score=72.0,
            relative_strength_score=65.0,
            liquidity_event_score=0.0,
            structure_event_score=68.0,
            momentum_shift_score=71.0,
            freshness_score=90.0,
            data_completeness_score=85.0,
        )
