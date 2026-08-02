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
from app.intelligence.early_bird.candidate_behavior_score import (
    CandidateBehaviorScore,
)

from test_early_bird_candidate_history_analyzer import (
    NOW,
)


def test_analyzer_returns_behavior_score():

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
            quality=80.0,
            whale_activity_score=70.0,
            open_interest_change_score=75.0,
            funding_divergence_score=50.0,
            volume_expansion_score=80.0,
            relative_strength_score=70.0,
            liquidity_event_score=0.0,
            structure_event_score=70.0,
            momentum_shift_score=75.0,
            freshness_score=95.0,
            data_completeness_score=90.0,
        )
    )

    result = CandidateHistoryAnalyzer().analyze(
        history
    )

    assert isinstance(
        result.behavior_score,
        CandidateBehaviorScore,
    )

    assert result.behavior_score.asset == "HYPE"
    assert (
        result.behavior_score.behavior_direction
        == "strengthening"
    )
