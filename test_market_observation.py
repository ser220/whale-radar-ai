from datetime import datetime, timezone, timedelta

import pytest

from app.intelligence.observations import (
    MarketObservation,
    MarketObservationType,
    ObservationSeverity,
)


def build_observation():
    return MarketObservation(
        observation_id="obs-001",
        asset="btcusdt",
        source="BINANCE",
        timeframe="24h",
        quality=90,
        observed_at=datetime(
            2026,
            7,
            17,
            12,
            0,
            tzinfo=timezone(timedelta(hours=2)),
        ),
        observation_kind=MarketObservationType.PRICE_MOVEMENT,
        severity=ObservationSeverity.MEDIUM,
        value=-2.21,
        reference_value=0.0,
    )


def test_market_observation_is_immutable():
    observation = build_observation()

    with pytest.raises(Exception):
        observation.value = 10


def test_timestamp_normalizes_to_utc():
    observation = build_observation()

    assert observation.observed_at.tzinfo == timezone.utc
    assert observation.observed_at.hour == 10


def test_enum_values_are_validated():
    observation = build_observation()

    assert (
        observation.observation_kind
        == MarketObservationType.PRICE_MOVEMENT
    )


def test_serialization_round_trip():
    observation = build_observation()

    payload = observation.to_dict()

    restored = MarketObservation.from_dict(payload)

    assert restored == observation


def test_invalid_numeric_value_rejected():
    with pytest.raises(Exception):
        MarketObservation(
            observation_id="obs-002",
            asset="BTCUSDT",
            source="BINANCE",
            timeframe="24h",
            quality=90,
            observed_at=datetime.now(timezone.utc),
            observation_kind=MarketObservationType.VOLUME_CHANGE,
            severity=ObservationSeverity.LOW,
            value=float("nan"),
        )
