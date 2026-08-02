from datetime import datetime, timezone

from app.intelligence.early_bird.candidate_observation import (
    EarlyBirdCandidateObservation,
)
from app.intelligence.early_bird.candidate_observation_store import (
    CandidateObservationStore,
)


NOW = datetime(
    2026,
    8,
    2,
    19,
    0,
    tzinfo=timezone.utc,
)


def observation(asset):
    return EarlyBirdCandidateObservation(
        asset=asset,
        observed_at=NOW,
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


def test_store_is_empty_initially():
    store = CandidateObservationStore()

    assert store.assets == ()


def test_store_creates_history_per_asset():
    store = CandidateObservationStore()

    btc = observation("BTC")
    hype = observation("HYPE")

    store.append(btc)
    store.append(hype)

    assert store.assets == (
        "BTC",
        "HYPE",
    )

    assert store.history("BTC").observations == (
        btc,
    )

    assert store.history("HYPE").observations == (
        hype,
    )


def test_unknown_asset_returns_none():
    store = CandidateObservationStore()

    assert store.history("SOL") is None
