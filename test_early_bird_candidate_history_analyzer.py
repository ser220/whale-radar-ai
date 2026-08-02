from datetime import datetime, timedelta, timezone

from app.intelligence.early_bird.candidate_history_analyzer import (
    CandidateHistoryAnalyzer,
)
from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)
from app.intelligence.early_bird.candidate_observation_history import (
    CandidateObservationHistory,
)


NOW = datetime(
    2026,
    8,
    2,
    19,
    30,
    tzinfo=timezone.utc,
)


def observation(
    *,
    observed_at,
    quality,
):
    return EarlyBirdCandidateObservation(
        asset="HYPE",
        observed_at=observed_at,
        quality=quality,
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


def test_analyzer_detects_rising_quality():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    history.append(
        observation(
            observed_at=NOW,
            quality=70.0,
        )
    )
    history.append(
        observation(
            observed_at=NOW + timedelta(minutes=15),
            quality=80.0,
        )
    )

    result = CandidateHistoryAnalyzer().analyze(
        history
    )

    assert result.asset == "HYPE"
    assert result.quality_change == 10.0
    assert result.quality_direction == "rising"


def test_analyzer_returns_insufficient_for_one_observation():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    history.append(
        observation(
            observed_at=NOW,
            quality=70.0,
        )
    )

    result = CandidateHistoryAnalyzer().analyze(
        history
    )

    assert result.quality_direction == "insufficient"
    assert result.quality_change is None


def test_analyzer_calculates_multi_factor_changes():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    first = EarlyBirdCandidateObservation(
        asset="HYPE",
        observed_at=NOW,
        quality=70.0,
        whale_activity_score=60.0,
        open_interest_change_score=50.0,
        funding_divergence_score=40.0,
        volume_expansion_score=55.0,
        relative_strength_score=65.0,
        liquidity_event_score=0.0,
        structure_event_score=60.0,
        momentum_shift_score=50.0,
        freshness_score=90.0,
        data_completeness_score=80.0,
    )

    second = EarlyBirdCandidateObservation(
        asset="HYPE",
        observed_at=NOW + timedelta(minutes=15),
        quality=80.0,
        whale_activity_score=68.0,
        open_interest_change_score=70.0,
        funding_divergence_score=45.0,
        volume_expansion_score=75.0,
        relative_strength_score=72.0,
        liquidity_event_score=0.0,
        structure_event_score=66.0,
        momentum_shift_score=65.0,
        freshness_score=94.0,
        data_completeness_score=90.0,
    )

    history.append(first)
    history.append(second)

    result = CandidateHistoryAnalyzer().analyze(
        history
    )

    assert result.open_interest_change == 20.0
    assert result.volume_expansion_change == 20.0
    assert result.funding_divergence_change == 5.0
    assert result.momentum_shift_change == 15.0
    assert result.data_completeness_change == 10.0


def test_analyzer_detects_strengthening_behavior():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    history.append(
        EarlyBirdCandidateObservation(
            asset="HYPE",
            observed_at=NOW,
            quality=60.0,
            whale_activity_score=55.0,
            open_interest_change_score=50.0,
            funding_divergence_score=40.0,
            volume_expansion_score=50.0,
            relative_strength_score=55.0,
            liquidity_event_score=0.0,
            structure_event_score=55.0,
            momentum_shift_score=50.0,
            freshness_score=90.0,
            data_completeness_score=80.0,
        )
    )

    history.append(
        EarlyBirdCandidateObservation(
            asset="HYPE",
            observed_at=NOW + timedelta(minutes=15),
            quality=75.0,
            whale_activity_score=65.0,
            open_interest_change_score=70.0,
            funding_divergence_score=48.0,
            volume_expansion_score=72.0,
            relative_strength_score=68.0,
            liquidity_event_score=0.0,
            structure_event_score=66.0,
            momentum_shift_score=69.0,
            freshness_score=94.0,
            data_completeness_score=90.0,
        )
    )

    result = CandidateHistoryAnalyzer().analyze(
        history
    )

    assert result.behavior_direction == "strengthening"
    assert result.positive_factor_count >= 4
    assert result.negative_factor_count == 0
