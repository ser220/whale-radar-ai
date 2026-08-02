from datetime import datetime, timedelta, timezone

import pytest

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
    18,
    30,
    tzinfo=timezone.utc,
)


def observation(
    *,
    asset="HYPE",
    observed_at=NOW,
    quality=80.0,
):
    return EarlyBirdCandidateObservation(
        asset=asset,
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


def test_history_is_empty_initially():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    assert history.asset == "HYPE"
    assert history.observations == ()


def test_history_appends_observations_in_order():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    first = observation(
        observed_at=NOW,
        quality=75.0,
    )
    second = observation(
        observed_at=NOW + timedelta(minutes=15),
        quality=82.0,
    )

    history.append(first)
    history.append(second)

    assert history.observations == (
        first,
        second,
    )


def test_history_rejects_other_asset():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    with pytest.raises(
        ValueError,
        match="observation asset must match history asset",
    ):
        history.append(
            observation(
                asset="BTC",
            )
        )


def test_history_rejects_duplicate_timestamp():
    history = CandidateObservationHistory(
        asset="HYPE",
    )

    history.append(
        observation(),
    )

    with pytest.raises(
        ValueError,
        match="observation timestamp already exists",
    ):
        history.append(
            observation(
                quality=90.0,
            )
        )


def test_history_retains_only_latest_observations():
    history = CandidateObservationHistory(
        asset="HYPE",
        max_observations=3,
    )

    values = tuple(
        observation(
            observed_at=NOW + timedelta(minutes=15 * index),
            quality=70.0 + index,
        )
        for index in range(4)
    )

    for value in values:
        history.append(value)

    assert history.observations == values[1:]
