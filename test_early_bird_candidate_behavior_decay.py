from datetime import timedelta

from app.intelligence.early_bird.candidate_history_analyzer import (
    CandidateHistoryAnalyzer,
)
from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)
from app.intelligence.early_bird.candidate_observation_history import (
    CandidateObservationHistory,
)

from test_early_bird_candidate_history_analyzer import NOW


def test_analyzer_detects_candidate_decay():

    history = CandidateObservationHistory(
        asset="HYPE",
    )

    history.append(
        EarlyBirdCandidateObservation(
            asset="HYPE",
            observed_at=NOW,
            quality=90.0,
            whale_activity_score=90.0,
            open_interest_change_score=85.0,
            funding_divergence_score=80.0,
            volume_expansion_score=90.0,
            relative_strength_score=85.0,
            liquidity_event_score=0.0,
            structure_event_score=80.0,
            momentum_shift_score=85.0,
            freshness_score=95.0,
            data_completeness_score=95.0,
        )
    )

    history.append(
        EarlyBirdCandidateObservation(
            asset="HYPE",
            observed_at=NOW + timedelta(minutes=15),
            quality=65.0,
            whale_activity_score=55.0,
            open_interest_change_score=30.0,
            funding_divergence_score=40.0,
            volume_expansion_score=35.0,
            relative_strength_score=60.0,
            liquidity_event_score=0.0,
            structure_event_score=55.0,
            momentum_shift_score=35.0,
            freshness_score=90.0,
            data_completeness_score=90.0,
        )
    )

    result = CandidateHistoryAnalyzer().analyze(
        history
    )

    assert result.behavior_score.behavior_direction == "weakening"
    assert result.behavior_score.decay_score > 0
    assert result.behavior_score.confidence > 50
